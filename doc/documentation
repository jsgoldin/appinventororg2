# AppInventor.org Documentation #

## General ##

### File Naming & Organization ###

#### Basics ####

Let's take a look at the directory structure.

The root directory contains some very important files that *should not be moved*.

We have:
	- app.yaml
	- index.yaml
	- app_controller.py
	
Additionally, we have a file called site_base.html.  This is the base template for most pages on the site, and includes the menu (side bar), top bar and footer.  There are actually two copies of this template.  There is a reason for this.  All of the dynamically generated pages (the apps) use *this* copy of the template.  To be able to place this template in another directory (something other than root) requires some complex configuration files.  I tried to do this, but it seemed overly complicated, and frankly, I couldn't get it to work.

Because of this, there is another copy of this template within the directory **/other**. If you make any changes to site_base.html, be sure to update both copies.  The HTML files within /other use the template located within that subdirectory.

Root also contains **app_base.html**, another very important file.  This is the basis (a second-level) template for all of the dynamic, "app," pages.  It should not be moved.

#### Assets ####

All assets for static pages are located within **/assets**, and should be pretty self-explanatory.  Assets used by the dynamic pages are contained in **/apps**.  This includes the APKs (Android source code) for those apps.

The **/appcarousel** subdir of /assets contains everything required by the carousel that appears in index.html.

#### Apps ####

Naming conventions for the apps are very important.  When you add an app to the site, you will assign it (on the app creation admin form) an **appId**. This appId is how the site "locates" resources related to a particular app.  This is because **app_base.html** contains references to resources that are named by appId.  For example, the hero image for each app page is referenced src="apps/{{ app.appId }}/hero.png".

When you create a new app, be sure to:
	- create a subdir within /apps, the name of which is the app Id.  So, for Hello Purr, the app ID is "hellopurr," so the subdir is also named that.
	- For Hello Purr, we would have the following names:
		- PDF is named hellopurr.pdf
		- zipfile is named hellopurr.zip
		- apk is named hellopurr.apk
	- Hero images are always simply named "hero" (as there is only one within any app's directory
	- QR images are named "qr"
	- The blocks images for the steps of the app are named block1.png, block2.png, block3.png, etc. (always PNG files only)
	
When you want to add some customization exercises, place the source zipfiles in the relevant app directory.  For the first customizations exercise, name it [appId]_custom1.zip, and [appId]_custom2.zip for the second one.
	
#### Docs ####

The **/doc** directory should be left alone, for the most part.  It includes this file, in addition to a license that is required to use Twitter's Bootstrap framework.

#### Static Pages ####

The **/static_pages** dir is divided according to the part of the site those files relate to. Should be pretty self-explanatory.  In order to standardize the look and feel of these pages more, going forward, I would recommend a more complex templating system using standardized div names coupled with Django "block" tags.  See the [Django doc] (https://docs.djangoproject.com/en/dev/topics/templates/) for more info.


## Admin Area ##

### Adding New Apps ###

To get to the admin area, simply enter "/Admin" (capital 'A') after the hostname.

This area is only accessible to those who are on the admin list for the site.  This can be changed by editing the app.yaml file, if you want to temporaily enable others to add apps.

- To add an app, just click the "Add/Mod App" button.
- To modify an existing app, click on the app you want to change (it will be highlighted), then click "Add/Mod App"
- The current values for all fields will appear in the forms.  You can change them as necessary.

### Adding Steps or Customization Exercises ###

Adding steps works in pretty much the same way as adding apps.  From the main admin page (where you add apps), just click on "Add Step" or "Add Custom."  You'll see a list of the existing steps/customization exercises.  Just click on one, then click "Add/Mod" to change it.

## The Datastore ##

The best way to add and edit apps, steps, and customs is via the admin forms, but you can also do this manually, if necessary.  To do this, just click on the Dashboard icon (far right) in the AppEngine Launcher, then click on the "datastore Viewer" link in the right-hand menu of the page that pops up.






  
	
		
			 




	