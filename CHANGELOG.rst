Changelog
=========

**1.3 (August 7, 2016)**

* Improved: bind to form submit event for more robust unlocking
* Improved: don't unlock admin for 'save and continue editing' form submissions
* Improved: only display connectivity warning once, after second API failure


**1.2 (March 21, 2016)**

* New: added `LOCKING_DELETE_TIMEOUT_SECONDS` setting
* Improved: reload rather than unlock form never owned by user to prevent accidental editing of  stale data
* Improved: removed unnecessary database call when loading form between saves
* Fixed: incorrect icon displaying on changelist view


**1.1 (February 16, 2016)**

* New: warn user when unable to save lock due to loss of Internet connectivity
* Improved: failed lock POST requests now return lock information
* Improved: styles
* Improved: reorganized admin JavaScript, improved linting
* Improved: database table name now user customizable in settings
* Fixed: plugin API now correctly passed `form` element instance
* Fixed: bug with click to take lock
* Fixed: `force_lock_for_user` correctly extends session
* Fixed: can no longer remove lock owned by other user
