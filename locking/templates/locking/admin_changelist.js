;(function (locking, undefined) {
    'use strict';

    var options = {{ options|safe }};
    var $ = locking.jQuery;
    var api = new locking.API({
            appLabel: options.appLabel,
            modelName: options.modelName,
        });

    $(document).ready(function () {
        function updateStatus () {
            api.ajax({success: function (data) {
                $('.locking-status').removeClass('locked');
                for (var i = 0; i < data.length; i++) {
                    $('#locking-' + data[i]['object_id']).addClass('locked');
                }
            }});
        };

        // Only run on changelist page
        if (document.getElementById('changelist')) {
            updateStatus();
            setInterval(updateStatus, options.ping * 1000);
        }
    });
})(window.locking);
