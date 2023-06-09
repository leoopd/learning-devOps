django will contain all beginner django projects.

### 05.06.23
Following the [tutorial](https://docs.djangoproject.com/en/4.2/intro/tutorial01/) to get a basic understanding of the framework

### 06.06.23
Adding www.ler0y.com to allowed hosts to log into the admin page

### 07.06.23
Login doesn't work yet
- adding host to `CSRF_TRUSTED_ORIGINS` to allow posts
- login works

### 08.06.23
Login works but the css doesn't load properly, trying to find out why

### 09.06.23
CSS still not loading properly, problem seems to be related to nginx serving of static files
- seems like it was a permissions problem
  - browser showed 403: Permission denied when trying to access css and such
  - nginx logs showed permission denied errors
  - chown the /static/ dir did not help

- moving the static dir to /var/www/ did the trick
  - css gets applied properly now
### Misc
For all helpful commands, random tips and tricks and whatever needs to be remembered
