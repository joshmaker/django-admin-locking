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
                    this.$form.prepend("<p class='errornote'>Form is locked</p>");
                }
                locking.LockingForm.prototype.disableForm.call(this);
            }
        });

        var lockingForm = new LockingAdminForm($form, {
            appLabel: options.appLabel,
            modelName: options.modelName,
            objectID: options.objectID
        });
    });
})(window.locking);
