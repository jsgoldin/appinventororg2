$(document).ready(function() {
	/* Highlight the module the user is currently in */
	current_content_title = $('.side-bar').attr('current_content_title')
	current_module_title = $('.side-bar').attr('current_module_title')
	
	var current_item = $(".item-text:contains('" + current_module_title + "')").parent()
			.parent();
	
	current_item.css('background-color', 'blue');
	current_item.find('a').css('color', 'white');
	current_item.children('span').removeClass('glyphicon-chevron-right');
	current_item.children('span').addClass('glyphicon-chevron-down');
	
	/* Highlight the lesson the user is currently in */
	$(".subject-sub-item-link:contains('" + current_content_title + "')").parent()
			.parent().css('font-weight', '900');
	
	
	/* hide the lessons for the other modules that the user is not currently in */
	$('.item-text:not(:contains(' + current_module_title + '))').parent().parent().parent().children('.sub-items-wrapper').each(function() {
		$(this).hide();
	});
	
	
	/* dropdown browse other modules via arrow button */
	$('.arrow').click(function() {
		if($(this).parent().text() == current_item.text()) {
			// special case if current item is clicked
			
			// toggle state of clicked item
			
			if(current_item.parent().children('.sub-items-wrapper').is(':hidden')) {
				// flip chevron
				current_item.children('span').removeClass('glyphicon-chevron-right');
				current_item.children('span').addClass('glyphicon-chevron-down');
				// slide down
				current_item.parent().children('.sub-items-wrapper').slideDown('fast');
			} else {
				// flip chevron
				current_item.children('span').removeClass('glyphicon-chevron-down');
				current_item.children('span').addClass('glyphicon-chevron-right');
				// slide up
				current_item.parent().children('.sub-items-wrapper').slideUp('fast');
			}
		} 
		else {
			// flip chevron of current item
			current_item.children('span').removeClass('glyphicon-chevron-down');
			current_item.children('span').addClass('glyphicon-chevron-right');
			// slide up current item sub items
			current_item.parent().children('.sub-items-wrapper').slideUp('fast');
		
			// slide down clicked on item's sub items and set it as the current_item
			$(this).parent().parent().children('.sub-items-wrapper').slideDown('fast');
		
			current_item = $(this).parent();
			// flip chevron of current item
			current_item.children('span').removeClass('glyphicon-chevron-right');
			current_item.children('span').addClass('glyphicon-chevron-down');
			
		}
	});
	
});

