/*
 * Contains functionality for the header navigation menu.
 * Requires Jquery.
 */


(function () {

    /* Contains jquery object of currently expanded menu item. If no menu item is expanded currentItem is null. */
    var currentItem = null;

    var curMegaMenuItem = null;


    function expandIfLinked(item) {
        var attr = item.attr("data-target");

        if (typeof attr !== typeof undefined && attr !== false) {
            // header item is linked to a drop down,
            // make it invisible

            $("#" + attr).addClass("visible");
        }
    }

    function unexpandIfLinked(item) {
        var attr = item.attr("data-target");


        if (typeof attr !== typeof undefined && attr !== false) {
            // header item is linked to a drop down,
            // make it invisible

            var itemToCollapse = $("#" + attr);


            itemToCollapse.removeClass("visible");

            // reset children
            itemToCollapse.children("ul").children(".selected-item").removeClass("selected-item");
        }
    }


    $(".slideout-menu > ul > li").click(function (e) {
        e.stopPropagation();
    });

    $(".header").click(function () {
        currentItem.parent().removeClass("selected-item");
        unexpandIfLinked(currentItem);
        currentItem = null;
    });


    $(".header-item").click(function (e) {
        e.stopPropagation();

        var newItem = $(this);
        var newParent = newItem.parent();


        var maybeMegaMenu = newParent.parent().parent();

        if (maybeMegaMenu.hasClass("mega-menu") && maybeMegaMenu.hasClass("visible")) {
            if (curMegaMenuItem == null) {
                newParent.addClass("selected-item");
                curMegaMenuItem = newItem;
            } else if (newItem.is(curMegaMenuItem)) {
                newParent.removeClass("selected-item");
                curMegaMenuItem = null;
            }
        } else {
            if (currentItem == null) {
                // nothing was open
                newParent.addClass("selected-item");
                currentItem = newItem;
                expandIfLinked(currentItem);
            } else if (newItem.is(currentItem)) {
                // clicked on current item to close current item
                newParent.removeClass("selected-item");
                unexpandIfLinked(currentItem);
                currentItem = null;
            } else {
                // item was already expanded when new item was clicked
                // item was open, clicked on another
                currentItem.parent().removeClass("selected-item");
                unexpandIfLinked(currentItem);

                newItem.parent().addClass("selected-item");
                currentItem = newItem;
                expandIfLinked(currentItem);
            }
        }
    });

// hover and stay selected behavior on mega-menus menus
    $(".mega-menu .slideout-menu > ul >li").hover(function () {
        $(".mega-menu .slideout-menu > ul >li").not($(this)).removeClass("selected-item");
        $(this).addClass("selected-item");
    });

})();