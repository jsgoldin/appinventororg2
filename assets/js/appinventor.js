/*
	A jquery plugin that simulates App Inventor in browser
	using an HTML5 canvas and some fancy javascript.

	A super work in progress...

	@author Jordan Goldin <jorgoldin@gmail.com>
*/



(function($) {
	$.fn.appinventor = function() {
		alert(this);

		return this;
	}

}(jQuery));



$(document).ready(function() {
	$("#myCanvas").appinventor();
});