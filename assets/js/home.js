

(function ( $ ) {
	
	/* Peekaboo
	 * 
	 * As the windows scrolls through the scroll zone an element will travel another zone
	 * in the opposite direction.
	 * 
	 *The peekabooer will move from hideBottom to hideTop.
	*/
    $.fn.peekaboo = function(scrollZoneTop, scrollZoneBottom, hideTop, hideBottom) {
    	
    	var hiderElem = $(this).detach();
    	
    	$("body").append(hiderElem);
    	
    	// Places hideElem's top at the hideBottom point.
    	// To fully expose the hideElem its top must be at
    	// hideBottom + hideElem.outerHeight()
    	hiderElem.css("top", hideBottom);

    	
    	var wallHeight = scrollZoneBottom - scrollZoneTop;
    	var hideHeight = hideBottom - hideTop;
    	
    	$(window).scroll(function() {
    		var jWindow = $(this);
    		var scrollBottom = jWindow.scrollTop() + jWindow.height()
    		

    		var newTop;
    		
    		console.log(scrollBottom + " !! " + scrollZoneTop);
    		
    		if (scrollBottom < scrollZoneTop) {
    			console.log("above");
    			newTop = hideTop;
    		} else if (scrollBottom > scrollZoneBottom) {
    			console.log("below");
    			newTop = hideBottom;
    		} else {
    			console.log("in");
    			var percentThroughWall = 1 - ((scrollZoneBottom - scrollBottom) / (scrollZoneBottom - scrollZoneTop));	    
	    		
    			console.log(percentThroughWall);
    			
	    		var hideElemOffset = percentThroughWall * (hideBottom - hideTop);
	    		
	    		console.log(percentThroughWall + " offset: " + hideElemOffset);
	    		
	    		newTop = hideTop + hideElemOffset;
    		}
    		
    		
    		hiderElem.css("top", newTop + "px");

    		
    	});
        return this;
    };
}( jQuery ));

$(document).ready(function() {
	var scrollStart = $(".landing-courses-section").offset().top;
	$(".peekaboo-robot").peekaboo(scrollStart, scrollStart + 400, scrollStart, scrollStart - 300);
});
