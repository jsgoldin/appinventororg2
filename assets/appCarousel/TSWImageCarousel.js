/* Copyright 2009-2010 Taco Software. All rights reserved.
 * http://tacosw.com
 *
 * This file is part of the Component Library included in Taco HTML Edit.
 * Licensed users of Taco HTML Edit may modify and use this source code 
 * for their web development (including commercial projects), as long as 
 * this copyright notice is retained.
 *
 * The contents of this file may not be published in a format intended
 * for access by other humans, so you may not put code examples on a
 * web site with all or part of the contents of this file, and you may
 * not publish the contents of this file in a printed format.
 */

function tswImageCarouselRight(id)
{
	tswImageCarouselGetForId(id).scrollRight();
}

function tswImageCarouselLeft(id)
{
	tswImageCarouselGetForId(id).scrollLeft();
}

function tswImageCarouselSelectPage(id, page)
{
	tswImageCarouselGetForId(id).selectPage(page);
}

var tswImageCarouselMap = new Object(); //maps image scroll id to TSWImageCarousel object;

//Returns the TSWImageCarousel object for an id, creating the object
//if necessary.
function tswImageCarouselGetForId(id)
{
	var imageScroll = tswImageCarouselMap[id];
	if(imageScroll == null)
	{
		imageScroll = new TSWImageCarousel(id);
		tswImageCarouselMap[id] = imageScroll;
	}
	return imageScroll;
}

//Invoked from setInterval to animate the scroll operation
function _tswImageCarouselAnimate(id)
{
	tswImageCarouselGetForId(id).animate();
}

//TSWImageCarousel is a javascript object that represents
//the image scroll component in the HTML document. The
//constructor takes the id of the object.
function TSWImageCarousel(id)
{
	this.id = id;
	this.selectedPage = 0; //The page that is currently selected
	
	//The total number of pages (before copying first page)
	this.numPages = TSWDomUtils.getChildrenWithTagName(this.getImageScrollContentElement(), 'div').length; 
	
	//Copy the first page to the end so that we can do wrap-around scrolling
	if(this.numPages > 0)
	{
		var content = this.getImageScrollContentElement();
		content.appendChild(TSWDomUtils.getChildrenWithTagName(content, 'div')[0].cloneNode(true));
	}
	
	//variables used in animation
	this.initialXOffset = 0; //The x offset of the scroll content when animation started
	this.targetXOffset = 0; //The targeted x offset for the animation
	
	this.animationStartDate; //date when the animation began
	this.animationIntervalId = null; //Identifies the interval timer being used for the animation
};
	
TSWImageCarousel.prototype.selectPage = function(page)
{
	this.unselectPageMarker(this.selectedPage);
	var scrollRight = page > this.selectedPage;
	this.selectedPage = page;
	this.selectPageMarker(this.selectedPage);
	
	this._setupAnimation(scrollRight);
};
	
TSWImageCarousel.prototype.scrollRight = function()
{
	this.unselectPageMarker(this.selectedPage);
	this.selectedPage = (this.selectedPage + 1) % this.numPages;
	this.selectPageMarker(this.selectedPage);
	
	this._setupAnimation(true);
};
	
TSWImageCarousel.prototype.scrollLeft = function()
{
	this.unselectPageMarker(this.selectedPage);
	this.selectedPage = this.selectedPage > 0 ? (this.selectedPage - 1) : (this.numPages - 1);
	this.selectPageMarker(this.selectedPage);
	
	this._setupAnimation(false);
};
	
TSWImageCarousel.prototype._setupAnimation = function(scrollRight)
{
	var scrollContent = this.getImageScrollContentElement();
	
	if(scrollContent.style.left != null && scrollContent.style.left != '')
	{
		this.initialXOffset = tswUtilsGetPixelsAsInteger(scrollContent.style.left);
	}
	this.animationStartDate = new Date();
	var pageWidth = this.getPageWidth();
	this.targetXOffset = -this.selectedPage*pageWidth;
	
	if(scrollRight)
	{
		//target must be less than initial
		if(this.targetXOffset > this.initialXOffset)
		{
			this.targetXOffset -= this.numPages*pageWidth
		}
	}
	else
	{
		//target must be greater than initial
		if(this.targetXOffset < this.initialXOffset)
		{
			this.targetXOffset += this.numPages*pageWidth
		}
	}
	
	if(this.animationIntervalId == null)
	{
		this.animationIntervalId = setInterval("_tswImageCarouselAnimate('"+this.id+"')", 25);
	}
};

TSWImageCarousel.prototype.unselectPageMarker = function(page)
{
	var pageMarker = this.getPageMarker(page);
	if(pageMarker != null)
	{
		pageMarker.className = 'tswImageCarouselPageMarkerUnselected';
	}
}

TSWImageCarousel.prototype.selectPageMarker = function(page)
{
	var pageMarker = this.getPageMarker(page);
	if(pageMarker != null)
	{
		pageMarker.className = 'tswImageCarouselPageMarkerSelected';
	}
}

TSWImageCarousel.prototype.getPageMarker = function(page)
{
	var pageMarkersElement = TSWDomUtils.getChildWithClassName(this.getImageScrollElement(), 'tswImageCarouselPageMarkers');
	if(pageMarkersElement != null && pageMarkersElement.className == 'tswImageCarouselPageMarkers')
	{
		var pageMarkersContainer = TSWDomUtils.getChildWithClassName(pageMarkersElement, 'tswImageCarouselPageMarkersContainer');
		var images = TSWDomUtils.getChildrenWithTagName(pageMarkersContainer, 'div');
		if(page >= 0 && page < images.length)
		{
			return images[page];
		}
	}
	return null;
};

TSWImageCarousel.prototype.getImageScrollElement = function()
{
	return document.getElementById(this.id);
};

TSWImageCarousel.prototype.getImageScrollContentElement = function()
{
	return TSWDomUtils.getChildWithClassName(this.getImageScrollElement(), 'tswImageCarouselContent');
};

TSWImageCarousel.prototype.getPageWidth = function()
{
	return this.getImageScrollElement().offsetWidth;
};

TSWImageCarousel.prototype.animate = function()
{
	var currentDate = new Date();
	var delta = (currentDate.getTime() - this.animationStartDate.getTime()) / 600.0;
	var pageWidth = this.getPageWidth();
	
	if(delta >= 1.0)
	{
		//complete the animation
		clearInterval(this.animationIntervalId);
		this.animationIntervalId = null;
		this.getImageScrollContentElement().style.left = String(-this.selectedPage*pageWidth) + 'px';
	}
	else
	{
		//continue animation
		var minXOffset = -(this.numPages)*pageWidth;
		
		var movementProgress = Math.sin(delta*Math.PI/2.0);
		var nextXOffset = movementProgress*this.targetXOffset + (1 - movementProgress)*this.initialXOffset;
		
		if(nextXOffset > 0.0)
		{
			nextXOffset -= this.numPages*pageWidth;
			this.initialXOffset -= this.numPages*pageWidth;
			this.targetXOffset -= this.numPages*pageWidth;
		}
		else if(nextXOffset < minXOffset)
		{
			nextXOffset += this.numPages*pageWidth;
			this.initialXOffset += this.numPages*pageWidth;
			this.targetXOffset += this.numPages*pageWidth;
		}
		
		this.getImageScrollContentElement().style.left = String(nextXOffset) + 'px';
	}
};

/* The checksum below is for internal use by Taco HTML Edit, 
   to detect if a component file has been modified.
   TacoHTMLEditChecksum: 65869967 */