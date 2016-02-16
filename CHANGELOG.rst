Changelog
=========

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
