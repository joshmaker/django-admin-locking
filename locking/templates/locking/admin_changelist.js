;(function (locking, undefined) {
    'use strict';

    var options = {{ options|safe }};
    var $ = locking.jQuery;
    $(document).ready(function () {
        $('.locking-status.locked').click(function () {
            var $lock = $(this);
            if (confirm("Are you sure you want to remove this lock?")) {
                var api = new locking.API({
                        appLabel: options.appLabel,
                        modelName: options.modelName,
                        objectID: $lock.data('object-id')
                    });
                api.unlock();
                $lock.removeClass('unlock').addClass('lock');
            }
        });
    });
})(window.locking);
