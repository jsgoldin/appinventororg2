/*
 * Contains functionality for the scroll to top and stop behavior on the sidebar in the content page.
 * Requires Jquery.
 */


/**
 * Scroll to top and stop behavior for the content page.
 */

$(document).ready(
    function () {


        var headerHeight = $('#header').outerHeight();
        var footerHeight = $("footer").outerHeight();
        var viewportHeight = $(window).outerHeight();

        

        var contentHeight = viewportHeight - headerHeight - footerHeight;

        alert(contentHeight);

        $(window).resize(function () {
            $('.vertical-content-nav-bar').height($(window).height());
        });

    });
