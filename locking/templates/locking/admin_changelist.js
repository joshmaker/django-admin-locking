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
                var user, name, lockedClass, lockedMessage;
                $('.locking-status').removeClass('locked').removeAttr('title');
                for (var i = 0; i < data.length; i++) {
                    user = data[i]['locked_by'];
                    if (user['username'] === options['currentUser']) {
                        lockedMessage = "You are currently editing this";
                        lockedClass = "editing";
                    } else {
                        name = user['first_name'] + ' ' + user['last_name'];
                        if (name === ' ') {
                            name = user['username'];
                        }
                        lockedMessage = 'Locked by ' + name + ' (' + user['email'] + ')';
                        lockedClass = "locked";
                    }
                    $('#locking-' + data[i]['object_id']).addClass(lockedClass).attr('title', lockedMessage);
                }
            }});
        };

        // Only run on changelist page
        if ($('.locking-status').length > 0) {
            updateStatus();
            setInterval(updateStatus, options.ping * 1000);
        }
        var cookieName = options.appLabel + options.modelName + 'unlock';
        $('.locking-status.locked').click(function () {
            locking.cookies.set(cookieName, '1', 60 * 1000);
        });
    });
})(window.locking);
