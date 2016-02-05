;(function (window) {
    'use strict';
    window.locking_test = {
        errors: [],
        onError: function(msg) {
            this.errors.push(msg);
        },
        confirmations: 0,
        alerts: 0
    };
    window.onerror = function(msg) {
        window.locking_test.onError(msg);
    };
    /* PhantomJS Doesn't have good support for confirming modal windows */
    window.confirm = function() {
        window.locking_test.confirmations++;
        return true;
    };
    window.alert = function() {
        window.locking_test.alerts++;
        return true;
    };

})(window);
