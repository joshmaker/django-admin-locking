;(function (locking, undefined) {
    'use strict';

    var options = {{ options|safe }};
    var $ = locking.jQuery;
    $(document).ready(function () {
        var $form = $('#' + options.modelName + '_form');
        var LockingAdminForm = function(form, opts) {
            this.init(form, opts);

            var cookieName = options.appLabel + options.modelName + 'unlock';
            if (locking.cookies.get(cookieName) === '1') {
                this.takeLock();
                locking.cookies.del(cookieName);
            }
        };
        $.extend(LockingAdminForm.prototype, locking.LockingForm.prototype);
        $.extend(LockingAdminForm.prototype, {
            warningHtml: '<ul class="messagelist grp-messagelist">' +
                            '<li class="warning grp-warning" id="locking-warning">' +
                                'Form is locked by <span class="locking-locked-by"></span>' +
                                '<a id="locking-take-lock" class="button grp-button" onclick="window.lockingForm.takeLock()">Take over lock</a>' +
                            '</li>' +
                         '</ul>',
            lockedBy: {
                setUp: function (data) {
                    this.name = data['username'];
                    if (data['first_name'] && data['last_name']) {
                        this.name = data['first_name'] + ' ' + data['last_name'];
                    }
                    this.email = data.email;
                }
            },
            disableForm: function() {
                if (!this.formDisabled) {
                    var self = this;

                    // Disable Delete link
                    $('.deletelink').css({'cursor': 'not-allowed', 'opacity': 0.5}).click(false);

                    // Add warning notice to form
                    this.$form.prepend(this.warningHtml);

                    // Lookup who has the lock
                    this.api.ajax({
                        success: function (data) {
                            self.lockedBy.setUp(data[0]['locked_by']);
                            $("#locking-warning .locking-locked-by").html(
                                self.lockedBy.name +
                                ' (<a href="mailto:' + self.lockedBy.email + '">' +
                                    self.lockedBy.email +
                                '</a>)'
                            );
                        }
                    });
                }
                locking.LockingForm.prototype.disableForm.call(this);
            },
            enableForm: function() {
                if (this.formDisabled) {
                    $('#locking-warning').parent().remove();
                }
                locking.LockingForm.prototype.enableForm.call(this);
            }
        });

        window.lockingForm = new LockingAdminForm($form, {
            appLabel: options.appLabel,
            modelName: options.modelName,
            objectID: options.objectID,
            ping: options.ping
        });
    });
})(window.locking);
