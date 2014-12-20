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

// highlight the content the user is currently on
current_content_ID = $('.vertical-content-nav-bar-title').attr(
		'current_content_ID');
current_item = $(
		".vertical-content-nav-bar-item[content_ID =" + current_content_ID
				+ "]").find('.vertical-content-nav-bar-item-text');
current_item.css('color', '#4F4F4F');
current_item.css('font-weight', '700');

// hover link arrow slide
$('.vertical-side-bar-top-box-back').hover(function() {
	icon = $(this).find('.glyphicon');
	icon.stop();
	icon.animate({
		right : "4px"
	}, 150);
}, function() {
	icon = $(this).find('.glyphicon');
	icon.stop();
	icon.animate({
		right : "0px"
	}, 150);
});

$('.vertical-side-bar-top-bottom-next').hover(function() {
	icon = $(this).find('.glyphicon');
	icon.stop();
	icon.animate({
		left : "6px"
	}, 150);
}, function() {
	icon = $(this).find('.glyphicon');
	icon.stop();
	icon.animate({
		left : "0px"
	}, 150);
});

// linkable vertical sidebar items
$('.vertical-side-bar-item').click(function() {
	window.location = $(this).attr('content_ID');
})

$('.vertical-side-bar-top-bottom-next').click(

		function() {
			url = String(document.URL).split('/');
			nextmod_id = $(this).attr('module_id');
			window.location = url[0] + '/' + url[1] + '/' + url[2] + '/'
					+ url[3] + '/' + url[4] + '/' + nextmod_id;
		});

$(document).ready(
		function() {
			// scroll top top then fixed
			$(window).bind('scroll', function() {
				var navHeight = $('#header-wrapper').height();
				var scrollBottom = $(window).scrollTop() + $(window).height();
				var topOfFooter = $("body").height() - $('footer').outerHeight();
				console.log("scrollBottom: " + scrollBottom + ", topOfFooter: " + topOfFooter);
				
				if ($(window).scrollTop() > navHeight) {
					$('.vertical-side-bar-container').addClass('fixed-sidebar');					
				} else {
					$('.vertical-side-bar-container').removeClass('fixed-sidebar');					
				}
				
				
				if (scrollBottom >= topOfFooter) {
					$('.vertical-side-bar-container').removeClass('fixed-sidebar');	
					$('.vertical-side-bar-container').addClass('fixed-sidebar-bottom');	
					$('.vertical-side-bar-container').css("bottom", $('footer').outerHeight());

				} else {
					$('.vertical-side-bar-container').removeClass('fixed-sidebar-bottom');
					$('.vertical-side-bar-container').css("bottom", "0px");

				}
				
			});

			// set height of vertical nav bar list thing
			$('.vertical-content-nav-bar').height($(window).height());

			// set min-height of content-area with weird padding to
			// prevent scroll to and fix
			// jump glitch
			$('#contentarea').css('min-height',
					$('.vertical-side-bar-container').height() + 10);

			$(window).resize(

			function() {
				$('.vertical-content-nav-bar').height($(window).height());
				// set height of scroll part of vertical nav bar
			});

		});
