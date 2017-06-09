;(function (locking, undefined) {
    'use strict';

    var $ = locking.jQuery;
    $(document).ready(function () {
        var options = {{ options|safe }}; // jshint ignore:line
        var $form = $('#' + options.modelName + '_form');

        locking.lockingFormInstance = new locking.LockingAdminForm($form, {
            apiURL: options.apiURL,
            appLabel: options.appLabel,
            modelName: options.modelName,
            ping: options.ping,
            messages: options.messages
        });
    });
})(window.locking);
