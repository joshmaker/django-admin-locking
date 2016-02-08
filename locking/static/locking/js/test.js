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

    /**
     * Polyfill for `Function.prototype.bind` missing from PhantomJS < 2.0
     * (Currently needed for tests to pass on Travis-CI)
     */
    if (!Function.prototype.bind) {
      Function.prototype.bind = function(oThis) {
        if (typeof this !== 'function') {
          // closest thing possible to the ECMAScript 5
          // internal IsCallable function
          throw new TypeError('Function.prototype.bind - what is trying to be bound is not callable');
        }

        var aArgs   = Array.prototype.slice.call(arguments, 1),
            fToBind = this,
            fNOP    = function() {},
            fBound  = function() {
              return fToBind.apply(this instanceof fNOP
                     ? this
                     : oThis,
                     aArgs.concat(Array.prototype.slice.call(arguments)));
            };

        if (this.prototype) {
          // Function.prototype don't have a prototype property
          fNOP.prototype = this.prototype; 
        }
        fBound.prototype = new fNOP();

        return fBound;
      };
    }

})(window);
