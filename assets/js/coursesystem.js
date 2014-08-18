/* The following is used on the courses pages */

// this function is used to translate a title to a url safe title
function wordToPrettyURL(word) {
	urlPrettyTitle = ""
	for (i = 0; i < word.length; i++) {
		if (word.charCodeAt(i) == 32) {
			urlPrettyTitle += '.'
		} else {
			urlPrettyTitle += word[i]
		}
	}
	return urlPrettyTitle;
}

// link to corresponding course page on course-box click
$('.course-box').click(function() {
	window.location = document.URL + "/" + $(this).attr('identifier');
});

// link to corresponding module page on module-box click
$('.module-box').click(
		function() {
			window.location = document.URL + "/"
					+ wordToPrettyURL($(this).attr('module_title'));
		});

// link to corresponding content page on module-box click
$('.content-box').click(
		function() {
			window.location = document.URL + "/"
					+ wordToPrettyURL($(this).attr('content_title'));
		});

// highlight hoverd items in vertical navbar
$('.vertical-content-nav-bar-item, .vertical-content-nav-bar-next-section-box')
		.hover(function() {
			$(this).css('background-color', '#FCFAC7');
		}, function() {
			$(this).css('background-color', '');
		});

// highlight the content the user is currently on
current_content_ID = $('.vertical-content-nav-bar-title').attr(
		'current_content_ID');
current_item = $(
		".vertical-content-nav-bar-item[content_ID =" + current_content_ID
				+ "]").find('.vertical-content-nav-bar-item-text');
current_item.css('color', '#4F4F4F');
current_item.css('font-weight', '700');

// linkable vertical sidebar items
$('.vertical-content-nav-bar-item').click(
		function() {
			if ($(this).attr('id') == 'modules_page') {
				newUrl = document.URL + "/" + $(this).attr('module_ID') + "/"
						+ $(this).attr('content_ID');
				window.location = newUrl;
			} else {
				window.location = $(this).attr('content_ID');
			}
		});

$('.vertical-content-nav-bar-next-section-box').click(
		function() {
			url = String(document.URL).split('/');
			nextmod_id = $(this).attr('module_id');
			window.location = url[0] + '/' + url[1] + '/' + url[2] + '/'
					+ url[3] + '/' + url[4] + '/' + nextmod_id;
		});

// back to course page button
$('.vertical-content-nav-bar-course-title-text').click(function() {
	url = String(document.URL).split('/');

	newURL = ""
	for (i = 0; i < url.length - 3; i++) {
		newURL += url[i] + "/";
	}

	newURL += url[i];

	window.location = newURL;
});



$(document).ready(function() {
	
	// scroll top top then fixed
	$(window).bind('scroll', function() {
		var navHeight = $('.banner-wrapper').height();
		if ($(window).scrollTop() > navHeight) {
			$('.vertical-content-nav-bar').addClass('fixed');
		} else {
			$('.vertical-content-nav-bar').removeClass('fixed');
		}
	});
	
	
	// set height of vertical nav bar list thing
	$('.vertical-content-nav-bar').height($(window).height());
	

	
	$( window ).resize(function() {
		$('.vertical-content-nav-bar').height($(window).height());
		// set height of scroll part of vertical nav bar
	});
	

	
	/* Tabbed module content browser functionality */
	
	
	// 

	// detect click on other tabs and switch to them
	$('.module-content-browser-box-tab-inner').click(function() {
		
		// hide the old one
		selected_tab = $('.module-content-browser-box-tab-inner[clicked="true"]');
		$('.course-modules-wrapper[module_id="' + selected_tab.attr('module_id') + '"]').hide();
		selected_tab.attr('clicked', 'false');
		selected_tab.removeClass('selected-tab');
		
		// show the new one
		$(this).attr('clicked', 'true');
		$(this).addClass('selected-tab');
		$('.course-modules-wrapper[module_id="' + $(this).attr('module_id') + '"]').show();		
		
	})
	


});