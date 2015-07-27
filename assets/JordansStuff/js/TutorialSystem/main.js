/* The following javascript is used by the TutorialSystem */

$(document).ready(function() {

	/* Highlight item boxes on hover */
	$(".item-box").mouseover(function() {
		$(this).addClass('hover');
	});

	$(".item-box").mouseout(function() {
		$(this).removeClass('hover');
	});

	/* Clickable modules that take you to corresponding content page */
	$(document).on('click', '#module', function() {
		window.location = "/modules/content?moduleid=" + $(this).attr('keyid');
	});
	
	/* Clickable content that take you to corresponding content display page */
	$(document).on('click', '#content', function() {
		window.location = "/modules/content/display?contentid=" + $(this).attr('keyid') + "&moduleid=" + $("#idholder").attr('keyid');
	});
	
	
	/* Highlight progress menu items on hover */
	$('.progress-menu-item').mouseover(function() {
		$(this).addClass('progress-hover');
	});
	
	$('.progress-menu-item').mouseout(function() {
		$(this).removeClass('progress-hover');
	});
	
	/* Link progress menu items to corresponding content display page */
	$('.progress-menu-item').click(function() {
		module_id = $('#modid').attr('keyid');
		content_id = $(this).attr('keyid');
		
		window.location = "/modules/content/display?contentid=" + content_id + "&moduleid=" + module_id;
	});
	
	/* Highlight current progress menu item */
	content_id = $('#contentid').attr('keyid');
	$('.progress-menu-item[keyid=' + content_id + ']').addClass('progress-current');
	

});
