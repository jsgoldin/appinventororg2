$(document).ready(function() {
	/* Highlight the module the user is currently in */
	current_content_title = $('.side-bar').attr('current_content_title')
	current_module_title = $('.side-bar').attr('current_module_title')
	
	
	var current_item = $(".item-text:contains('" + current_module_title + "')").parent()
			.parent();
	
	current_item.find('.side-bar-item').css('background-color', '#5BA4CA');
	current_item.find('.item-text').css('color', 'white');
	current_item.find('.side-bar-item').children('span').removeClass('glyphicon-chevron-right');
	current_item.find('.side-bar-item').children('span').addClass('glyphicon-chevron-down');
	
	
	/* hide the lessons for the other modules that the user is not currently in */
	$('.item-text:not(:contains(' + current_module_title + '))').parent().parent().children('.sub-items-wrapper').each(function() {
		$(this).hide();
	});
	
	
	/* when the user hovers over an item that is not the current item */
	$(".module-content-wrapper").hover(function() {
		if($(this).text() == current_item.text()) {
				// alert('the same!');
		} else {
			// show the hovered item's sub items
			$(this).children('.sub-items-wrapper').slideDown('fast');
			
			// get position of first sub-item
			// var position = $(this).children('.side-bar-item').offset();
			
			$(this).children('.side-bar-item').children('span').removeClass('glyphicon-chevron-right');
			$(this).children('.side-bar-item').children('span').addClass('glyphicon-chevron-down');
			
		}
	}, function() {
		if($(this).text() == current_item.text()) {
			// alert('the same!');
		} else {
			$(this).children('.sub-items-wrapper').slideUp('fast');
				
			$(this).children('.side-bar-item').children('span').removeClass('glyphicon-chevron-down');
			$(this).children('.side-bar-item').children('span').addClass('glyphicon-chevron-right');
		}
	});
	
	
	/* highlight sub-items */
	$('.side-bar-sub-item').hover(function() {
		$(this).css('background-color', '#F0F8FC');
	}, function() {
		$(this).css('background-color', '');
	});
	
	
});

