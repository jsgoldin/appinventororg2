/**
 * Translate a title to a url safe title
 */
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


/**
 * link to corresponding course page on course-box click
 */
$('.course-box').click(function() {
	window.location = document.URL + "/" + $(this).attr('identifier');
});

/**
 * link to corresponding module page on module-box click
 */
$('.module-box').click(
		function() {
			window.location = document.URL + "/"
					+ wordToPrettyURL($(this).attr('module_title'));
		});

/**
 * link to corresponding content page on module-box click
 */
$('.content-box').click(
		function() {
			window.location = document.URL + "/"
					+ wordToPrettyURL($(this).attr('content_title'));
		});

/**
 * More general hover link slide. Finds icon within class and slides it. Name a
 * class slide-left or slide-right for it to work.
 */
$('.slide-left').hover(function() {
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

$('.slide-right').hover(function() {
	icon = $(this).find('.glyphicon');
	icon.stop();
	icon.animate({
		left : "10px"
	}, 150);
}, function() {
	icon = $(this).find('.glyphicon');
	icon.stop();
	icon.animate({
		left : "0px"
	}, 150);
});

/**
 * Hover link arrow slide
 */
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

/**
 * Hover link arrow slide
 */
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

/**
 * Linkable vertical sidebar items
 */
$('.vertical-side-bar-item').click(function() {
	window.location = $(this).attr('content_ID');
})

/**
 * Linkable vertical sidebar items
 */
$('.vertical-side-bar-top-bottom-next').click(
		function() {
			url = String(document.URL).split('/');
			nextmod_id = $(this).attr('module_id');
			window.location = url[0] + '/' + url[1] + '/' + url[2] + '/'
					+ url[3] + '/' + url[4] + '/' + nextmod_id;
		});

/**
 * Scroll to top and stop behavior for the content page.
 */

			
$(document).ready(
		function() {

			


			// scroll top top then fixed
			$(window).bind(
					'scroll',

					function() {

						// do not run on mobile devices
						if ($(window).width() > 767) {

							var headerHeight = $('#header-wrapper').height();

							var scrollBottom = $(window).scrollTop()
									+ $(window).height();

							var topOfFooter = $(document).height()
									- $('footer').outerHeight();

							if ($(window).scrollTop() < headerHeight
									&& scrollBottom >= topOfFooter) {
								// WEIRD EDGE CASE ON SHORT PAGES!!!!!
								console.log("EDGE CASE!!!!!");
							} else {
								if ($(window).scrollTop() >= headerHeight) {
									// scrollTop is below header
									// sidebar should be fixed

									$('.vertical-side-bar-container').addClass(
											'fixed-sidebar-top');
								} else {
									// scrollTop is not below header
									// sidebar should not be fixed
									$('.vertical-side-bar-container')
											.removeClass('fixed-sidebar-top');
								}

								if (scrollBottom >= topOfFooter) {
									$('.vertical-side-bar-container')
											.removeClass('fixed-sidebar-top');

									$('.vertical-side-bar-container').addClass(
											'sidebar-bottom');

									var targetTopPos = $(document).height()
											- $(window).height()
											- $('footer').outerHeight();

									$('.vertical-side-bar-container').css(
											"top", targetTopPos);
								} else {
									$('.vertical-side-bar-container')
											.removeClass('sidebar-bottom');
									$('.vertical-side-bar-container').css(
											"top", "auto");
								}
							}

						}
					});

			// set height of vertical nav bar list thing
			$('.vertical-content-nav-bar').height($(window).height());

			$(window).resize(function() {
				$('.vertical-content-nav-bar').height($(window).height());
			});

		});


