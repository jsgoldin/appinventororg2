/*
 * Contains functionality for the scroll to top and stop behavior on the sidebar in the content page.
 * Requires Jquery.
 */

/**
 * Scroll to top and stop behavior for the content page.
 */

$(document).ready(function() {

	var headerHeight = $('#header').outerHeight();
	var footerHeight = $("footer").outerHeight();

	var topOfFooter = $(document).height() - footerHeight;

	var m_window = $(window);

	var sideBar = $('#vertical-side-bar');

	m_window.bind("scroll", function() {

		var scrollTop = m_window.scrollTop();
		var scrollBottom = scrollTop + m_window.height();

		// must update on every scroll because of lag loading
		// content.
		topOfFooter = $(document).height() - footerHeight;

		if (scrollTop < headerHeight && scrollBottom >= topOfFooter) {
			// WEIRD EDGE CASE ON SHORT PAGES!!!!!

		} else {

			if (m_window.scrollTop() >= headerHeight) {
				// scrollTop is below header
				// sidebar should be fixed

				sideBar.addClass('fixed-sidebar-top');
			} else {
				// scrollTop is not below header
				// sidebar should not be fixed
				sideBar.removeClass('fixed-sidebar-top');
			}

			if (scrollBottom >= topOfFooter) {

				sideBar.removeClass('fixed-sidebar-top');

				sideBar.addClass('sidebar-bottom');

				sideBar.css("bottom", footerHeight);
			} else {
				sideBar.removeClass('sidebar-bottom');
				sideBar.css("bottom", "auto");
			}
		}

	});
});
