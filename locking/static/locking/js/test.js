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
})(window);
