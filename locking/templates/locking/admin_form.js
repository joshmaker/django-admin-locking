;(function (locking, undefined) {
    'use strict';

    var options = {{ options|safe }};
    var $ = locking.jQuery;
    $(document).ready(function () {
        var $form = $('#' + options.modelName + '_form');
        var LockingAdminForm = function(form, opts) {
            this.init(form, opts);
        };
        $.extend(LockingAdminForm.prototype, locking.LockingForm.prototype);
        $.extend(LockingAdminForm.prototype, {
            disableForm: function() {
                if (!this.formDisabled) {
                    // Disable Delete link
                    // $('.deletelink').css({'cursor': 'not-allowed', 'opacity': 0.5}).click(false);

                    this.$form.prepend('<ul class="messagelist"><li class="warning" id="locking-errornote">Form is locked</li></ul>');
                    this.api.ajax({
                        success: function (data) {
                            var locker = data[0]['locked_by'],
                                lockerName = locker.username;
                            if (locker['first_name'] && locker['last_name']) {
                                lockerName = locker['first_name'] + ' ' + locker['last_name'];
                            }
                            $("#locking-errornote").html('Form is locked by ' +
                                                          lockerName +
                                                          ' (<a href="mailto:' + locker.email + '">' +
                                                            locker.email +
                                                          '</a>)');
                        }
                    });
                }
                locking.LockingForm.prototype.disableForm.call(this);
            }
        });

        var lockingForm = new LockingAdminForm($form, {
            appLabel: options.appLabel,
            modelName: options.modelName,
            objectID: options.objectID,
            ping: options.ping
        });
    });
})(window.locking);
