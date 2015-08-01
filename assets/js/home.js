

(function ( $ ) {
	
	/* Peekaboo
	 * 
	 * As the windows scrolls through the scroll zone an element will travel another zone
	 * in the opposite direction.
	 * 
	 * The peekabooer will move from hideTopPos to hideBtmPos.
	 *
	 * TODO: ability to update positions, this is useful if the window changes size and the 
	 * scroll zone or hide path needs to change with it.
	 *
	*/
    $.fn.peekaboo = function(scrollZoneTop, scrollZoneBottom, hideBtmPos, hideTopPos) {
    	
    	var hiderElem = $(this).detach();
    	
    	$("body").append(hiderElem);
    	
    	// Places hideElem's top at the hideBtmPos point.
    	// To fully expose the hideElem its top must be at
    	// hideBtmPos + hideElem.outerHeight()
    	hiderElem.css("top", hideBtmPos);

    	var wallHeight = scrollZoneBottom - scrollZoneTop;
    	var hideHeight = hideTopPos - hideBtmPos;
    	
    	$(window).scroll(function() {
    		var jWindow = $(this);
    		var scrollBottom = jWindow.scrollTop() + jWindow.height()
    		var newTop;
    		
    		if (scrollBottom < scrollZoneTop) {
    			newTop = hideBtmPos;
    		} else if (scrollBottom > scrollZoneBottom) {
    			newTop = hideTopPos;
    		} else {
    			var percentThroughWall = 1 - ((scrollZoneBottom - scrollBottom) / (scrollZoneBottom - scrollZoneTop));	    
	    		var hideElemOffset = percentThroughWall * (hideTopPos - hideBtmPos);	    		
	    		newTop = hideBtmPos + hideElemOffset;
    		}
    		
    		hiderElem.css("top", newTop + "px");
    	});
        return this;
    };
}( jQuery ));

$(document).ready(function() {
	var scrollStart = $(".landing-courses-section").offset().top + 80;
	$(".peekaboo-robot").peekaboo(scrollStart, scrollStart + 300, scrollStart,scrollStart - 300);
});
