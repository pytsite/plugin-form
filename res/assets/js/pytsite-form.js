require(['jquery', 'pytsite-form-module', 'assetman'], function ($, form, assetman) {
    $('.pytsite-form').each(function () {
        // Create form
        const frm = new form.Form($(this));

        // If requested to walk to particular step automatically
        const h = assetman.parseLocation().hash;
        const walkToStep = '__form_step' in h ? parseInt(h['__form_step']) : 1;
        $(frm.em).on('forward:form:pytsite', function () {
            // When form will make its first step, move it automatically to the requested step
            if (frm.currentStep < walkToStep)
                frm.forward();
        });

        // Do the first step
        frm.forward();
    });
});
