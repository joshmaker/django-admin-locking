;(function (locking, undefined) {
    'use strict';

    var options = {{ options|safe }};
    var $ = locking.jQuery;
    $(document).ready(function () {
        alert(options);
    });
})(window.locking);
