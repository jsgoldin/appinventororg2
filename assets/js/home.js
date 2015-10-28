(function($) {

	/*
	 * Peekaboo
	 * 
	 * As the windows scrolls through the scroll zone an element will travel
	 * another zone in the opposite direction. The scrollzone is determined by
	 * the position of 2 jquery objects. The hideZone is determined by another 2
	 * jquery objects. The peekabooer will move from hideTopPosObj to
	 * hideBtmPosObj.
	 */

	$.fn.peekaboo = function(scrollZoneTopObj, scrollZoneBottomObj,
			hideBtmPosObj, hideTopPosObj) {

		var scrollZoneTop;
		var scrollZoneBottom;
		var hideBtmPos;
		var hideTopPos;

		var wallHeight;
		var hideHeight;

		var scrollBottom;

		var m_window = $(window);

		function updateScrollZones(m_window, scrollZoneTopObj, hideBtmPosObj,
				hideTopPosObj) {
			scrollBottom = m_window.scrollTop() + m_window.height();
			scrollZoneTop = scrollZoneTopObj.offset().top;
			scrollZoneBottom = scrollZoneBottomObj.offset().top;
			hideBtmPos = hideBtmPosObj.offset().top;
			hideTopPos = hideTopPosObj.offset().top;

			wallHeight = scrollZoneBottom - scrollZoneTop;
			hideHeight = hideTopPos - hideBtmPos;
		}

		function updatePeekABooPos(scrollBottom, scrollZoneTop,
				scrollZoneBottom, hideTopPos, hideBtmPos) {
			var newTop;

			if (scrollBottom < scrollZoneTop) {
				newTop = hideBtmPos;
			} else if (scrollBottom > scrollZoneBottom) {
				newTop = hideTopPos;
			} else {
				var percentThroughWall = 1 - ((scrollZoneBottom - scrollBottom) / (scrollZoneBottom - scrollZoneTop));
				var hideElemOffset = percentThroughWall
						* (hideTopPos - hideBtmPos);
				newTop = hideBtmPos + hideElemOffset;
			}
			hiderElem.css("top", newTop + "px");
		}

		// initialize peekaboo elements initial position
		var hiderElem = $(this).detach();
		$("body").append(hiderElem);
		hideBtmPos = hideBtmPosObj.offset().top;

		// Places hideElem's top at the hideBtmPos point.
		// To fully expose the hideElem its top must be at
		// hideBtmPos + hideElem.outerHeight()
		hiderElem.css("position", "absolute");
		hiderElem.css("top", hideBtmPos);

		m_window.scroll(function() {
			updateScrollZones(m_window, scrollZoneTopObj, hideBtmPosObj,
					hideTopPosObj);
			updatePeekABooPos(scrollBottom, scrollZoneTop, scrollZoneBottom,
					hideTopPos, hideBtmPos);
		});

		m_window.resize(function() {
			updateScrollZones(m_window, scrollZoneTopObj, hideBtmPosObj,
					hideTopPosObj);
			updatePeekABooPos(scrollBottom, scrollZoneTop, scrollZoneBottom,
					hideTopPos, hideBtmPos);
		});

		return this;
	};
	
	
	/*
	 * Force an absolute position object with dynamic width
	 * to stay centered.
	*/
	
	$.fn.centerAbsolute = function() {
		
		var objToCenter = this;
		
		var m_window = $(window);
		
	
		function center(m_window, objToCenter) {
			// calculate negative left offset
			var halfObjWidth = objToCenter.width() / 2;
			var halfWindowWidth = m_window.width() / 2;
				
			var newLeft = -1 * (halfObjWidth - halfWindowWidth);
			
			objToCenter.css("left", newLeft);
			
		}
		
		center(m_window, objToCenter);
		
		m_window.resize(function() {
			center(m_window, objToCenter);
		});
		
		objToCenter.resize(function() {
			center(m_window, objToCenter);
		})
		
		
		return this;
	}

}(jQuery));

$(document).ready(function() {
		
		var scrollStart = $(".landing-courses-section").offset().top + 80;
		$(".peekaboo-robot").peekaboo($("#scrollZoneTopObj"),
				$("#scrollZoneBottomObj"), $("#hideBtmPosObj"),
				$("#hideTopPosObj"));
		
		$(".landing-video-section video").centerAbsolute();

		$("#landing-slideshow").owlCarousel({});
});
