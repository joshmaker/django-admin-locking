;(function (locking, undefined) {
    'use strict';

    var $ = locking.jQuery;
    $(document).ready(function () {
        // Django makes it tricky to load JS on only the changelist page,
        // so we check for the .locking-status column to ensure we aren't on the
        // changeform instead
        if ($('.locking-status').length) {
            var options = {{ options|safe }}; // jshint ignore:line

            locking.changeListViewInstance = new locking.ChangeListView({
                apiURL: options.apiURL,
                appLabel: options.appLabel,
                modelName: options.modelName,
                ping: options.ping,
                currentUser: options.currentUser,
                messages: options.messages
            });
        }
    });
})(window.locking);
