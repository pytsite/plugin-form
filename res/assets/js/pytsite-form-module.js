define(['jquery', 'jquery-scrollto', 'assetman', 'http-api', 'widget'], function ($, scrollTo, assetman, httpApi, widget) {
    let forms = {};

    const htmlEntityMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '/': '&#x2F;',
        '`': '&#x60;',
        '=': '&#x3D;'
    };

    function escapeHtml(s) {
        return String(s).replace(/[&<>"'`=\/]/g, function (s) {
            return htmlEntityMap[s];
        });
    }

    function getForm(id) {
        if (id in forms)
            return forms[id];
        else
            throw "Form '" + id + "' is not found";
    }

    function Form(em) {
        let self = this;
        self.em = em;
        self.id = em.attr('id');
        self.name = em.attr('name');
        self.enctype = em.attr('enctype');
        self.action = em.attr('action');
        self.method = em.attr('method') || 'POST';
        self.location = location.origin + location.pathname;
        self.weight = parseInt(em.data('weight'));
        self.getWidgetsEp = em.data('getWidgetsEp');
        self.validationEp = em.data('validationEp');
        self.updateLocationHash = em.data('updateLocationHash') === 'True';
        self.totalSteps = em.data('steps');
        self.currentStep = 0;
        self.isCurrentStepValidated = true;
        self.readyToSubmit = false;
        self.areas = {};
        self.title = em.find('.form-title');
        self.messages = em.find('.form-messages').first();
        self.widgets = {};
        self.assets = em.data('assets').split(',');

        // Load assets
        $.each(self.assets, function (i, asset) {
            assetman.load(asset, null);
        });

        // Form ID can be passed via query
        if (self.updateLocationHash) {
            const h = assetman.parseLocation().hash;
            if ('__form_uid' in h) {
                self.id = h['__form_uid'];
                em.attr('id', self.id);
            }
            else {
                h['__form_uid'] = self.id;
                window.location.hash = $.param(h);
            }
        }

        // Initialize areas
        em.find('.form-area').each(function () {
            self.areas[$(this).data('formArea')] = $(this);
        });

        // Form submit event handler
        self.em.submit(function (event) {
            event.preventDefault();

            // Clear form's messages
            self.clearMessages();

            // Form isn't ready to submit, just move one step forward.
            if (!self.readyToSubmit) {
                self.forward();
            }
            // Form is ready to submit
            else {
                // Notify listeners about upcoming form submit
                self.em.trigger('formPreSubmit', [self]);

                const submitButton = self.em.find('[type=submit]');
                submitButton.attr('disabled', true);

                httpApi.post(self.action, self.serialize()).done(function (r) {
                    self.em.trigger('formSubmit', [self, r]);

                    if (r.hasOwnProperty('__alert'))
                        window.alert(r.__alert);

                    if (r.hasOwnProperty('__reset') && r.__reset)
                        self.reset();

                    if (r.hasOwnProperty('__redirect'))
                        window.location.href = r.__redirect;
                }).fail(function (e) {
                    self.em.trigger('formSubmitError', [self, e]);

                    if (e.hasOwnProperty('responseJSON')) {
                        if (e.responseJSON.hasOwnProperty('warning')) {
                            self.addMessage(e.responseJSON.warning, 'warning');
                            $(window).scrollTo(self.messages, 250);
                        }

                        if (e.responseJSON.hasOwnProperty('error')) {
                            self.addMessage(e.responseJSON.error, 'danger');
                            $(window).scrollTo(self.messages, 250);
                        }
                    }

                    submitButton.attr('disabled', false);
                });

            }
        });

        /**
         * Serialize form
         *
         * @param {bool} skipTags
         * @returns {Object}
         */
        self.serialize = function (skipTags) {
            function getEmValue(em) {
                if (em.tagName === 'INPUT' && em.type === 'checkbox')
                    return em.checked ? em.value : null;
                else
                    return em.value;
            }

            let r = {};

            // Process every element which has 'name'
            self.em.find('[name]').each(function () {
                const emVal = getEmValue(this);

                if (emVal === null)
                    return;

                if (skipTags instanceof Array && this.tagName in skipTags)
                    return;

                if ($(this).attr('data-skip-serialization') === 'True')
                    return;

                const dictListMatch = this.name.match(/([^\[]+)\[(\w+)]\[]$/);
                const listMatch = this.name.match(/\[]$/);

                let fName = this.name;
                if (dictListMatch)
                    fName = dictListMatch[1];

                if (!(fName in r)) {
                    if (dictListMatch) {
                        r[fName] = {};
                        r[fName][dictListMatch[2]] = [emVal];
                    }
                    else if (listMatch)
                        r[fName] = [emVal];
                    else
                        r[fName] = emVal;
                }
                else {
                    if (dictListMatch) {
                        if (!(dictListMatch[2] in r[fName]))
                            r[fName][dictListMatch[2]] = [];
                        r[fName][dictListMatch[2]].push(emVal);
                    }
                    else if (listMatch)
                        r[fName].push(emVal);
                    else
                        r[fName] = emVal;
                }
            });

            for (const k in r) {
                if (r.hasOwnProperty(k) && r[k] instanceof Array && r[k].length === 1)
                    r[k] = r[k][0];
            }

            return r;
        };

        /**
         * Do an AJAX request
         *
         * @param {String} method
         * @param {String} ep
         * @returns {Promise}
         * @private
         */
        self._request = function (method, ep) {
            const data = self.serialize();

            // Merge data from location query
            $.extend(data, assetman.parseLocation(true).query);

            return httpApi.request(method, ep, data).fail(function (resp) {
                if ('responseJSON' in resp && 'error' in resp.responseJSON)
                    self.addMessage(resp.responseJSON.error, 'danger');
                else
                    self.addMessage(resp.statusText, 'danger');
            });
        };

        /**
         * Count form's widgets for the step
         *
         * @param {Number} step
         * @returns {Number}
         */
        self.countWidgets = function (step) {
            let r = 0;

            for (const uid in self.widgets) {
                if (self.widgets.hasOwnProperty(uid) && self.widgets[uid].formStep === step)
                    ++r;
            }

            return r;
        };

        /**
         * Set form's title
         *
         * @param {String} title
         */
        self.setTitle = function (title) {
            self.title.html('<h4>' + title + '</h4>');
        };

        /**
         * Clear form's messages
         */
        self.clearMessages = function () {
            self.messages.html('');
        };

        /**
         * Add a message to the form
         *
         * @param {String} msg
         * @param {String} type
         */
        self.addMessage = function (msg, type) {
            if (!type)
                type = 'info';

            msg = escapeHtml(msg);

            self.messages.append('<div class="alert alert-' + type + '" role="alert">' + msg + '</div>')
        };

        /**
         * Create and place a widget on the form
         *
         * @param {String} html
         * @returns {widget.Widget}
         */
        self.addWidget = function (html) {
            // Create widget object
            const w = new widget.Widget(html);

            // Initially widget is hidden
            w.hide();

            // Widget replaces another one with different UID
            if (w.replaces === w.uid)
                self.removeWidget(w.uid);

            // Widget replaces another one with same UID
            if (w.uid in self.widgets)
                self.removeWidget(w.uid);

            // Append widget to the list of loaded widgets
            self.widgets[w.uid] = w;

            // To prevent HTML elements IDs overlapping in case of presence more than one form on the same page
            w.em.find('[id][id!=""]').each(function () {
                $(this).attr('id', self.name + '_' + $(this).attr('id'));
            });
            w.em.find('label[for]').each(function () {
                $(this).attr('for', self.name + '_' + $(this).attr('for'));
            });

            // Append widget's element to the form's HTML tree
            if (w.parentUid)
                self.getWidget(w.parentUid).appendChild(w);
            else
                self.areas[w.formArea].append(w.em);

            return w
        };

        /**
         * Get a widget of the form
         *
         * @param {String} uid
         * @returns {widget.Widget}
         */
        self.getWidget = function (uid) {
            if (!(uid in self.widgets))
                throw "Widget '" + uid + "' does not exist";

            return self.widgets[uid];
        };

        /**
         * Remove a widget from the form
         *
         * @param {String} uid
         */
        self.removeWidget = function (uid) {
            if (!(uid in self.widgets))
                return;

            self.widgets[uid].em.remove();
            delete self.widgets[uid];
        };

        /**
         * Load widgets for the step
         *
         * @param {Number} step
         * @returns {Promise}
         */
        self.loadWidgets = function (step) {
            const deffer = $.Deferred();

            self._request('POST', self.getWidgetsEp + '/' + self.id + '/' + step).done(function (resp) {
                const numWidgetsToInit = resp.length;

                for (let i = 0; i < numWidgetsToInit; i++) {
                    // Create widget from raw HTML string
                    let w = self.addWidget(resp[i]);

                    // Set form's step of the widget
                    w.formStep = step;
                }

                if (self.countWidgets(step) === numWidgetsToInit)
                    deffer.resolve();
                else
                    throw 'Something went wrong';
            });

            return deffer;
        };

        /**
         * Fill form's widgets with values
         *
         * @param {Object} data
         * @returns {Form}
         */
        self.fill = function (data) {
            for (const k in data) {
                if (data.hasOwnProperty(k))
                    self.em.find('[name="' + k + '"]').val(data[k]);
            }

            return self;
        };

        /**
         * Do form validation
         *
         * @returns {Promise}
         */
        self.validate = function () {
            const deffer = $.Deferred();

            // Mark current step as validated when validation will finish
            deffer.done(function () {
                self.isCurrentStepValidated = true;
            });

            if (self.currentStep > 0) {
                // Clear form's messages
                self.clearMessages();

                // Reset widgets state
                for (const uid in self.widgets)
                    self.widgets[uid].clearState().clearMessages();

                const ep = self.validationEp + '/' + self.id + '/' + self.currentStep;
                self._request('POST', ep).done(function (resp) {
                    if (resp.status) {
                        deffer.resolve();
                    }
                    else {
                        // Add error messages for widgets
                        for (const widget_uid in resp.messages) {
                            if (!resp.messages.hasOwnProperty(widget_uid))
                                continue;

                            let w, widget_message;

                            if (widget_uid in self.widgets) {
                                w = self.widgets[widget_uid];
                            }

                            // Convert single message to array
                            if (typeof resp.messages[widget_uid] === 'string') {
                                resp.messages[widget_uid] = [resp.messages[widget_uid]];
                            }

                            // Iterate over multiple messages for the same widget
                            for (let i = 0; i < resp.messages[widget_uid].length; i++) {
                                widget_message = resp.messages[widget_uid][i];

                                // If widget exists
                                if (w) {
                                    if (!w.alwaysHidden) {
                                        w.setState('error');
                                        w.addMessage(widget_message, 'danger');
                                    }
                                    else {
                                        self.addMessage(widget_uid + ': ' + widget_message, 'danger');
                                    }
                                }
                                // Widget does not exist
                                else {
                                    self.addMessage(widget_uid + ': ' + widget_message, 'danger');
                                }
                            }
                        }


                        let scrollToTarget = self.em.find('.has-error').first();
                        if (!scrollToTarget.length)
                            scrollToTarget = self.messages;

                        $(window).scrollTo(scrollToTarget, 250);
                        deffer.reject();
                    }
                }).fail(function () {
                    $(window).scrollTo(0, 250);
                    deffer.reject();
                });
            }
            else {
                deffer.resolve();
            }

            return deffer;
        };

        /**
         * Show widgets for the step
         *
         * @param {Number} step
         * @returns {Form}
         */
        self.showWidgets = function (step) {
            for (const uid in self.widgets) {
                if (self.widgets[uid].formStep === step)
                    self.widgets[uid].show();
            }

            return self;
        };

        /**
         * Hide widgets for the step
         *
         * @param {Number} step
         * @returns {Form}
         */
        self.hideWidgets = function (step) {
            for (const uid in self.widgets) {
                if (self.widgets[uid].formStep === step)
                    self.widgets[uid].hide();
            }

            return self;
        };

        /**
         * Remove widgets of the step
         *
         * @param {Number} step
         * @returns {Form}
         */
        self.removeWidgets = function (step) {
            for (const uid in self.widgets) {
                if (self.widgets[uid].formStep === step)
                    self.removeWidget(uid);
            }

            return self;
        };

        /**
         * Move to the next step
         *
         * @returns {Promise}
         */
        self.forward = function () {
            const deffer = $.Deferred();
            const submitButton = self.em.find('[type=submit]');

            // Disable user activity while widgets are loading
            submitButton.attr('disabled', true);

            // Validating the form for the current step
            self.validate().done(function () {
                // It is not a last step, so just load and show widgets for the next step
                if (self.currentStep < self.totalSteps) {
                    // Hide widgets for the current step
                    self.hideWidgets(self.currentStep);

                    // Increase current step
                    ++self.currentStep;
                    if (self.updateLocationHash && self.totalSteps > 1) {
                        const h = assetman.parseLocation().hash;
                        h['__form_step'] = self.currentStep;
                        window.location.hash = $.param(h);
                    }

                    // Load widgets for the current step
                    self.loadWidgets(self.currentStep).done(function () {
                        // Attach click handler to the 'Backward' button
                        self.em.find('.form-action-backward').click(self.backward);

                        // Mark current step as is not validated
                        self.isCurrentStepValidated = false;

                        // Show widgets
                        self.showWidgets(self.currentStep);

                        // Notify listeners
                        $(self.em).trigger('formForward', [self]);
                        deffer.resolve();

                        // Scroll to top of the page
                        if (self.currentStep > 1) {
                            $.scrollTo(self.em, 250);
                        }

                        // Enable submit button
                        submitButton.attr('disabled', false);
                    });
                }
                // It is a last step, just allowing submit the form
                else {
                    self.readyToSubmit = true;
                    self.em.submit();
                    submitButton.attr('disabled', false);
                }
            }).fail(function () {
                submitButton.attr('disabled', false);
                deffer.reject();
            });

            return deffer;
        };

        /**
         * Move to the previous step
         */
        self.backward = function () {
            self.removeWidgets(self.currentStep);
            self.showWidgets(--self.currentStep);

            if (self.updateLocationHash && self.totalSteps > 1) {
                const h = assetman.parseLocation().hash;
                h['__form_step'] = self.currentStep;
                window.location.hash = $.param(h);
            }

            $.scrollTo(self.em, 250);
        };

        /**
         * Reset form's HTML element
         *
         * @returns {Form}
         */
        self.reset = function () {
            self.em[0].reset();

            return self;
        }
    }

    return {
        Form: Form,
        getForm: getForm
    }
});
