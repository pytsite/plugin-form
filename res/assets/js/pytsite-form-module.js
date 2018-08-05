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

    class Form {
        constructor(em) {
            this.em = em;
            this.uid = em.attr('id');
            this.name = em.attr('name');
            this.enctype = em.attr('enctype');
            this.action = em.attr('action');
            this.method = em.attr('method') || 'POST';
            this.location = location.origin + location.pathname;
            this.weight = parseInt(em.data('weight'));
            this.getWidgetsEp = em.data('getWidgetsEp');
            this.validationEp = em.data('validationEp');
            this.updateLocationHash = em.data('updateLocationHash') === 'True';
            this.totalSteps = em.data('steps');
            this.currentStep = 0;
            this.isCurrentStepValidated = true;
            this.readyToSubmit = false;
            this.areas = {};
            this.title = em.find('.form-title');
            this.messages = em.find('.form-messages').first();
            this.widgets = {};
            this.assets = em.data('assets').split(',');

            // Load assets
            $.each(this.assets, function (i, asset) {
                assetman.load(asset, null);
            });

            // Form ID can be passed via query
            if (this.updateLocationHash) {
                const h = assetman.parseLocation().hash;
                if ('__form_uid' in h) {
                    this.uid = h['__form_uid'];
                    em.attr('id', this.uid);
                }
                else {
                    h['__form_uid'] = this.uid;
                    window.location.hash = $.param(h);
                }
            }

            const self = this;

            // Initialize areas
            em.find('.form-area').each(function () {
                self.areas[$(this).data('formArea')] = $(this);
            });

            // Form submit event handler
            this.em.submit(function (event) {
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
        }

        /**
         * Serialize form
         *
         * @param {bool} skipTags
         * @returns {Object}
         */
        serialize(skipTags = []) {
            function getEmValue(em) {
                if (em.tagName === 'INPUT' && em.type === 'checkbox')
                    return em.checked ? em.value : null;
                else
                    return em.value;
            }

            let r = {};

            // Process every element which has 'name'
            this.em.find('[name]').each(function () {
                const emVal = getEmValue(this);

                if (emVal === null)
                    return;

                if (this.tagName in skipTags)
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

            for (let k in r) {
                if (r.hasOwnProperty(k) && r[k] instanceof Array && r[k].length === 1)
                    r[k] = r[k][0];
            }

            return r;
        };

        /**
         * Do an AJAX request
         *
         * @param {string} method
         * @param {string} ep
         * @returns {Promise}
         * @private
         */
        _request(method, ep) {
            const data = this.serialize();
            const self = this;

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
         * @param {number} step
         * @returns {number}
         */
        countWidgets(step) {
            let r = 0;

            $.each(this.widgets, (i, w) => {
                if (w.formStep === step)
                    ++r;
            });

            return r;
        };

        /**
         * Set form's title
         *
         * @param {string} title
         */
        setTitle(title) {
            this.title.html('<h4>' + title + '</h4>');
        };

        /**
         * Clear form's messages
         */
        clearMessages() {
            this.messages.html('');
        };

        /**
         * Add a message to the form
         *
         * @param {string} msg
         * @param {string} type
         */
        addMessage(msg, type) {
            if (!type)
                type = 'info';

            msg = escapeHtml(msg);

            this.messages.append('<div class="alert alert-' + type + '" role="alert">' + msg + '</div>')
        };

        /**
         * Create and place a widget on the form
         *
         * @param {string} html
         * @return {widget.Widget}
         */
        addWidget(html) {
            // Create widget object
            const w = new widget.Widget(html);

            // Make widget's UID unique
            w.uid = `${this.uid}_${w.uid}`;

            // Update widget's parent UID unique
            if (w.parentUid)
                w.parentUid = `${this.uid}_${w.parentUid}`;

            // Initially widget is hidden
            w.hide();

            // Widget replaces another one with different UID
            if (w.replaces === w.uid)
                this.removeWidget(w.uid);

            // Widget replaces another one with same UID
            if (w.uid in this.widgets)
                this.removeWidget(w.uid);

            // Append widget to the list of loaded widgets
            this.widgets[w.uid] = w;

            // Append widget's element to the form's HTML tree
            if (w.parentUid)
                this.getWidget(w.parentUid).appendChild(w);
            else
                this.areas[w.formArea].append(w.em);

            return w
        };

        /**
         * Get a widget of the form
         *
         * @param {string} uid
         * @returns {widget.Widget}
         */
        getWidget(uid) {
            if (!(uid in this.widgets))
                throw "Widget '" + uid + "' does not exist";

            return this.widgets[uid];
        };

        /**
         * Remove a widget from the form
         *
         * @param {string} uid
         */
        removeWidget(uid) {
            if (!(uid in this.widgets))
                return;

            this.widgets[uid].em.remove();
            delete this.widgets[uid];
        };

        /**
         * Load widgets for the step
         *
         * @param {Number} step
         * @returns {Promise}
         */
        loadWidgets(step) {
            const self = this;
            const deffer = $.Deferred();

            this._request('POST', this.getWidgetsEp + '/' + this.uid + '/' + step).done(function (resp) {
                const widgetsToLoadCnt = resp.length;

                for (let i = 0; i < widgetsToLoadCnt; i++) {
                    // Create widget from raw HTML string
                    let w = self.addWidget(resp[i]);

                    // Set form's step of the widget
                    w.formStep = step;
                }

                const loadedWidgetsCnt = self.countWidgets(step);
                if (loadedWidgetsCnt === widgetsToLoadCnt)
                    deffer.resolve();
                else
                    throw 'Expected widgets to load: ' + widgetsToLoadCnt + ', loaded:' + loadedWidgetsCnt;
            });

            return deffer;
        };

        /**
         * Fill form's widgets with values
         *
         * @param {Object} data
         * @returns {Form}
         */
        fill(data) {
            for (let k in data) {
                if (data.hasOwnProperty(k))
                    this.em.find('[name="' + k + '"]').val(data[k]);
            }

            return this;
        };

        /**
         * Do form validation
         *
         * @returns {Promise}
         */
        validate() {
            const self = this;
            const deffer = $.Deferred();

            // Mark current step as validated when validation will finish
            deffer.done(function () {
                self.isCurrentStepValidated = true;
            });

            if (this.currentStep > 0) {
                // Clear form's messages
                self.clearMessages();

                // Reset widgets state
                $.each(self.widgets, (i, w) => {
                    w.clearState().clearMessages();
                });

                const ep = self.validationEp + '/' + self.uid + '/' + self.currentStep;
                self._request('POST', ep).done(function (resp) {
                    if (resp.status) {
                        deffer.resolve();
                    }
                    else {
                        // Add error messages for widgets
                        for (let widget_uid in resp.messages) {
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
        showWidgets(step) {
            $.each(this.widgets, (i, w) => {
                if (w.formStep === step)
                    w.show();
            });

            return this;
        };

        /**
         * Hide widgets for the step
         *
         * @param {Number} step
         * @returns {Form}
         */
        hideWidgets(step) {
            $.each(this.widgets, (i, w) => {
                if (w.formStep === step)
                    w.hide();
            });

            return this;
        };

        /**
         * Remove widgets of the step
         *
         * @param {Number} step
         * @returns {Form}
         */
        removeWidgets(step) {
            const self = this;

            $.each(self.widgets, (i, w) => {
                if (w.formStep === step)
                    self.removeWidget(w.uid);
            });

            return this;
        };

        /**
         * Move to the next step
         *
         * @returns {Promise}
         */
        forward() {
            const self = this;
            const deffer = $.Deferred();
            const submitButton = this.em.find('[type=submit]');

            // Disable user activity while widgets are loading
            submitButton.attr('disabled', true);

            // Validating the form for the current step
            this.validate().done(function () {
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
        backward() {
            this.removeWidgets(this.currentStep);
            this.showWidgets(--this.currentStep);

            if (this.updateLocationHash && this.totalSteps > 1) {
                const h = assetman.parseLocation().hash;
                h['__form_step'] = this.currentStep;
                window.location.hash = $.param(h);
            }

            $.scrollTo(this.em, 250);
        };

        /**
         * Reset form's HTML element
         *
         * @returns {Form}
         */
        reset() {
            this.em[0].reset();

            return this;
        }
    }

    return {
        Form: Form,
        getForm: getForm
    }
});
