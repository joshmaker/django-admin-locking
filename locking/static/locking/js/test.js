;(function (window) {
    'use strict';
    window.locking_test = {
        errors: [],
        onError: function(msg) {
            this.errors.push(msg);
        }
    }
    window.onerror = function(msg) {
        locking_test.onError(msg);
    }
})(window);
