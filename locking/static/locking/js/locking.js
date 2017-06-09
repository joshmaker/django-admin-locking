;(function(window, document, undefined) {
    'use strict';

    /**
     * Global locking object
     *
     * Setup the global locking object and attach jQuery to it.
     * Multiple versions of jQuery may be installed, and we want
     * to ensure that all locking code is using the same version.
     */
    window.locking = window.locking || {};
    var locking = window.locking;
    if (locking.jQuery === undefined) {
        locking.jQuery = (window.django !== undefined && django.jQuery !== undefined) ? django.jQuery : jQuery;
    }
    var $ = locking.jQuery;

    /**
     * Locking API Wrapper
     *
     * Makes asynchronous calls to lock or unlock an object
     */
    locking.API = function(apiURL, messages) {
        this.apiURL = apiURL;
        this.lockWasTakenByUserText = messages.lockWasTakenByUserText;
        this.confirmTakeLockText = messages.confirmTakeLockText;
        this.networkWarningText = messages.networkWarningText;
    };
    locking.ajax = {
        num_pending: 0,
        has_pending: function () {
            return (this.num_pending > 0);
        }
    };
    $.extend(locking.API.prototype, {
        ajax: function(opts) {
            var defaults = {
                url: this.apiURL,
                async: true,
                cache: false
            };
            var self = this;
            this._onAjaxStart();
            if ('complete' in opts) {
                if (!$.isArray(opts.complete)) {
                    opts.complete = [opts.complete];
                }
            } else {
                opts.complete = [];
            }
            opts.complete.push(self._onAjaxEnd);
            $.ajax($.extend(defaults, opts));
        },
        lock: function(opts) {
            this.ajax($.extend({'type': 'POST'}, opts));
        },
        unlock: function(opts) {
            this.ajax($.extend({'type': 'DELETE'}, opts));
        },
        takeLock: function(opts) {
            this.ajax($.extend({'type': 'PUT'}, opts));
        },
        _onAjaxStart: function() {
            locking.ajax.num_pending++;
        },
        _onAjaxEnd: function() {
            locking.ajax.num_pending--;
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
         * Add custom enable / disable rules for plugins
         * @param [...object] takes plugin objects that have both an 'enable'
         *                    and 'disable' method
         */
        register: function() {
            for (var i = 0; i < arguments.length; i++) {
                var plugin = arguments[i];
                if (typeof plugin.enable !== 'function' || typeof plugin.disable !== 'function') {
                    throw new Error("Plugin passed to register missing either 'enable' or 'disable' method");
                }
                this.plugins.push(plugin);
            }
        },

        /**
         * Call any custom enable rules
         * @param element    the form that has it's inputs enabled
         */
        enable: function(form) {
            var numPlugins = this.plugins.length;
            for (var i = 0; i < numPlugins; i++) {
                this.plugins[i].enable(form);
            }
        },

        /**
         * Call any custom disable rules
         * @param element    the form that has it's inputs 
         */
        disable: function(form) {
            var numPlugins = this.plugins.length;
            for (var i = 0; i < numPlugins; i++) {
                this.plugins[i].disable(form);
            }
        }
    };

    /**
     * LockingForm
     *
     * Used to setup locking on a given HTML form.
     * Will attempt to create a lock on the related object on initialization
     * and then again every `self.ping` number of seconds.
     */
    locking.LockingForm = function(form, opts) {
        this.init(form, opts);
    };
    $.extend(locking.LockingForm.prototype, {
        hasLock: false,
        hasHadLock: false,
        formDisabled: false,
        numFailedConnections: 0,
        removeLockOnUnload: true,
        init: function(form, opts) {
            var self = this;
            this.ping = opts.ping;
            this.$form = $(form);
            this.api = new locking.API(opts.apiURL, opts.messages);
            this.confirmTakeLockText = opts.messages.confirmTakeLockText;
            this.networkWarningText = opts.messages.networkWarningText;
            this.lockWasTakenByUserText = opts.messages.lockWasTakenByUserText;

            // Attempt to get a lock
            this.getLock();

            // Attempt to get / maintain a lock ever ping number of seconds
            setInterval(function() { self.getLock(); }, self.ping * 1000);

            // Unlock the form when leaving the page
            $(window).on('beforeunload submit', function() {
                if (self.hasLock && self.removeLockOnUnload) {
                    // We have to assure that our unlock request gets
                    // through before the user leaves the page, so it
                    // shouldn't run asynchronously.
                    self.api.unlock({'async': false});
                    self.hasLock = false;
                }
            });
        },

        /**
         * API Call to attempt to get a lock on this form
         * and then enable or disable the inputs on this form
         */
        getLock: function() {
            var self = this;
            this.api.lock({
                success: function() {
                    self.enableForm();
                },
                error: function(XMLHttpRequest) {
                    if (XMLHttpRequest.status < 200 || XMLHttpRequest.status >= 500) {
                        if (self.hasLock && self.numFailedConnections == 1) {
                            window.alert(self.networkWarningText);
                        }
                        self.numFailedConnections++;
                    } else {
                        if (self.hasLock) {
                            window.alert(self.lockWasTakenByUserText);
                        }
                        self.disableForm($.parseJSON(XMLHttpRequest.responseText));
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
                locking.LockingFormPlugins.disable(this.$form[0]);

                // Finish with standard disabling
                $disabledInputs.attr('disabled', 'disabled');

                this.$disabledInputs = $disabledInputs;
                $(document).trigger('locking:form-disabled');
                this.formDisabled = true;
            }
            this.hasLock = false;
        },

        /**
         * Enable all fields locked by `disableForm`
         */
        enableForm: function() {
            if (this.formDisabled) {
                if (this.hasHadLock) {
                    // Allow form submission
                    this.$form.off('submit', this.preventFormSubmission);

                    // Enable all standard fields
                    this.$disabledInputs.removeAttr('disabled');

                    // Execute custom enabling rules
                    locking.LockingFormPlugins.enable(this.$form[0]);

                    $(document).trigger('locking:form-enabled');
                    this.formDisabled = false;
                } else {
                    location.reload();
                }
            }
            this.hasLock = true;
            this.hasHadLock = true;
        },

        takeLock: function() {
            if (window.confirm(this.confirmTakeLockText)) {
                var self = this;
                this.api.takeLock({
                    success: function() {
                        self.enableForm();
                    }
                });
            }
        }
    });

    locking.cookies = {
        set: function(name, value, expires) {
            var d = new Date();
            d.setTime(d.getTime() + expires);
            var expires = "expires="+d.toGMTString();
            document.cookie = name + "=" + value + "; " + expires + "; path=/";
        },
        get: function(name) {
            var value = "; " + document.cookie;
            var parts = value.split("; " + name + "=");
            if (parts.length == 2) {
                return parts.pop().split(";").shift();
            }
        },
        del: function(name) {
            this.set(name, '', 0);
        }
    };

})(window, document);
