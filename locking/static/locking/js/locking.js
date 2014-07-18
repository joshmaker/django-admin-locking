;(function(window, document, undefined) {
    'use strict';

    /**
     * Global locking object
     *
     * Setup the global locking object and attach jQuery to it.
     * Multiple versions of jquery may be installed, and we want
     * to ensure that all locking code is using the same version.
     */
    window.locking = window.locking || {};
    if (locking.jQuery === undefined) {
        locking.jQuery = (window.django !== undefined && django.jQuery !== undefined) ? django.jQuery : jQuery;
    }
    var $ = locking.jQuery;

    /**
     * Locking API Wrapper
     *
     * Makes asyncronous calls to lock or unlock an object
     */
    locking.API = function(opts) {
        this.init(opts);
    };
    $.extend(locking.API.prototype, {
        defaults: {
            hostURL: null,
            apiBaseURL: '/locking/api/lock',
            appLabel: null,
            modelName: null,
            objectID: null
        },
        init: function(opts) {
            opts = $.extend(this.defaults, opts);
            this.hostURL = $.grep(
                [opts.hostURL, opts.apiBaseURL, opts.appLabel, opts.modelName, opts.objectID],
                function(x) { return !!(x); }
            ).join('/') + '/';
        },
        ajax: function(opts) {
            var defaults = {
                url: this.hostURL,
                async: true,
                cache: false
            };
            $.ajax($.extend(defaults, opts));
        },
        lock: function(opts) {
            this.ajax($.extend({'type': 'POST'}, opts));
        },
        unlock: function(opts) {
            this.ajax($.extend({'type': 'DELETE'}, opts));
        }
    });

    /**
     * Locking Form Plugin Registry
     *
     * Some form widgets may require custom logic for enabling / disabling them
     */
    locking.LockingFormPlugins = {
        /**
         * List of custom enable / disable rules for special form inputs
         */
        plugins: [],

        /**
         * Add custom enable / disable rules
         * @param {Function} enableFn function to enable some JS input widget
         * @param {Function} disableFn function to disable some JS input widget
         *                   return any :input fields disabled by this function
         */
        register: function(enableFn, disableFn) {
            this.plugins.push({
                enable: enableFn,
                disable: disableFn
            });
        }
    };

    /**
     * LockingForm
     *
     * Used to setup locking on a given HTML form.
     * Will attempt to create a lock on the related object on initialization
     * and then again every 15 seconds.
     */
    locking.LockingForm = function(form, opts) {
        this.init(form, opts);
    };
    $.extend(locking.LockingForm.prototype, {
        hasLock: false,
        formDisabled: false,
        init: function(form, opts) {
            var self = this;

            this.$form = $(form);
            this.api = new locking.API({
                appLabel: opts.appLabel,
                modelName: opts.modelName,
                objectID: opts.objectID
            });

            // Attempt to get a lock
            this.getLock();

            // Attempt to get / maintain a lock every 15 seconds
            setTimeout(function() { self.getLock(); }, 15000);

            // Unlock the form when leaving the page
            $(window).on('beforeunload', function() {
                if (self.hasLock) {
                    // We have to assure that our unlock request gets
                    // through before the user leaves the page, so it
                    // shouldn't run asynchronously.
                    self.api.unlock({'async': false});
                }
            });
        },

        /**
         * API Call to attempt to get a lock on this form
         * and then enable or disbale the inputs on this form
         */
        getLock: function() {
            var self = this;
            this.api.lock({
                statusCode: {
                    200: function() {
                        self.hasLock = true;
                        self.enabledForm();
                    },
                    401: function() {
                        self.disableForm();
                    }
                }
            });
        },

        preventFormSubmission: function(event) {
            event.preventDefault();
        },

        /**
         * Disable all fields that aren't already disabled
         */
        disableForm: function() {
            if (!this.formDisabled) {

                // Disable form submission
                this.$form.on('submit', this.preventFormSubmission);

                // Don't touch inputs that are disabled independently of locking
                // We don't cache the list of alreadyDisable inputs because they
                // might have changed due to other JS libraries
                var $alreadyDisabled = this.$form.find(":input[disabled]");
                var $disabledInputs = this.$form.find(":input").not($alreadyDisabled);

                // Execute custom disabling rules
                var numPlugins = locking.LockingFormPlugins.length;
                for (var i = 0; i < numPlugins; i++) {
                    $disabledInputs = $disabledInputs.not(locking.LockingFormPlugins[i].disable(this.$form));
                }

                // Finish with standard disabling
                $disabledInputs.attr('disabled', 'disabled');

                this.$disabledInputs = $disabledInputs;
                $(document).trigger('locking:form-disabled');
                this.formDisabled = true;
            }
        },

        /**
         * Enable all fields locked by `disableForm`
         */
        enabledForm: function() {
            if (this.formDisabled) {

                // Allow form submission
                this.$form.off('submit', this.preventFormSubmission);

                // Enable all standard fields
                this.$disabledInputs.removeAttr('disabled');

                // Execute custom enabling rules
                var numPlugins = locking.LockingFormPlugins.length;
                for (var i = 0; i < numPlugins; i++) {
                    locking.LockingFormPlugins[i].enable(this.$form);
                }

                $(document).trigger('locking:form-enabled');
                this.formDisabled = false;
            }
        }
    });

})(window, document);
