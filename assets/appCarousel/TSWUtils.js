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

var tswUtilsComponentResourcesDirectory = null;

function tswUtilsGetResourcesDirectory()
{
	if(tswUtilsComponentResourcesDirectory == null)
	{
		//if tswUtilsComponentResourcesDirectory is undefined, check for a script
		//referenced from the document named "TSWUtils.js". Determine the components
		//path from it.
		var scripts = document.getElementsByTagName('script');
		for(var i=0; i<scripts.length; i++)
		{
			var scriptTag = scripts[i];
			var scriptSrc = scriptTag.getAttribute('src');
			if(scriptSrc != null)
			{
				var fileNameIndex = scriptSrc.indexOf('TSWUtils.js');
				if(fileNameIndex != -1)
				{
					tswUtilsComponentResourcesDirectory = scriptSrc.substr(0, fileNameIndex);
					break;
				}
			}
		}
	}
	return tswUtilsComponentResourcesDirectory;
}

//Set the style left, top, width, and height of an element
function tswUtilsSetDimensions(element, coords)
{
	element.style.left = coords[0]+'px';
	element.style.top = coords[1]+'px';
	element.style.width = coords[2]+'px';
	element.style.height = coords[3]+'px';
}

//Set the opacity of an element; alpha is a value
//between 0.0 (transparent) and 1.0 (opaque)
function tswUtilsSetOpacity(element, alpha) {
	element.style.opacity = alpha; //for Safari, Firefox
	element.style.filter = 'alpha(opacity=' + alpha*100.0 + ')'; //for IE
}

//Preload an image, calling the appropriate callback when the operation is complete.
//The callback is passed the Image object as a parameter.
function tswUtilsPreloadImage(imageObject, imageUrl, successCallback, errorCallback, context)
{
	if(successCallback != null)
	{
		imageObject.onload = function() {successCallback(imageObject, context)};
	}
	if(errorCallback != null)
	{
		imageObject.onerror = function() {errorCallback(imageObject, context)};
		imageObject.onabort = function() {errorCallback(imageObject, context)};
	}
	
	imageObject.src = imageUrl;
	return imageObject;
}

function tswUtilsIsBody(element)
{
	return (/^(?:body|html)$/i).test(element.tagName);
}

function tswUtilsBorderBox(element)
{
	return tswUtilsGetStyle(element, '-moz-box-sizing') == 'border-box';
}

function tswUtilsTopBorder(element)
{
	return parseInt(tswUtilsGetStyle(element, 'border-top-width'));
}

function tswUtilsLeftBorder(element)
{
	return parseInt(tswUtilsGetStyle(element, 'border-left-width'));
}

function tswUtilsGetScroll(element)
{
	if(tswUtilsIsBody(element)) 
	{
		var win = window;
		doc = (!element.ownerDocument.compatMode || element.ownerDocument.compatMode == 'CSS1Compat') ? 
		element.ownerDocument.getElementsByTagName('html')[0] : element.ownerDocument.body;
		return {x: win.pageXOffset || doc.scrollLeft, y: win.pageYOffset || doc.scrollTop};
	}
	return {x: element.scrollLeft, y: element.scrollTop};
}

//Returns [x,y] pair for the position of an element on screen.
function tswUtilsGetAbsolutePosition(element)
{
	//Code adapted from MooTools Element.getOffsets()
	if(element.getBoundingClientRect)
	{
		var bound = element.getBoundingClientRect(),
		html = element.ownerDocument.documentElement,
		scroll = tswUtilsGetScroll(html),
		isFixed = (tswUtilsGetStyle(element, 'position') == 'fixed');
		return [
				parseInt(bound.left, 10) + ((isFixed) ? 0 : scroll.x) - html.clientLeft,
				parseInt(bound.top, 10) +  ((isFixed) ? 0 : scroll.y) - html.clientTop
				];
	}
	
	
	var pos = [0, 0];
	var orig = element;
	var isGecko = (document.getBoxObjectFor == undefined || element.clientTop == undefined) ? false : true; //Firefox 3+
	var isWebkit = (navigator.taintEnabled) ? false : true;
	if (tswUtilsIsBody(element)) return pos;
	
	while (element && !tswUtilsIsBody(element))
	{
		pos[0] += element.offsetLeft;
		pos[1] += element.offsetTop;
		
		if(isGecko)
		{
			if(!tswUtilsBorderBox(element))
			{
				pos[0] += tswUtilsLeftBorder(element);
				pos[1] += tswUtilsTopBorder(element);
			}
			var parent = element.parentNode;
			if(parent && tswUtilsGetStyle(parent, 'overflow') != 'visible')
			{
				pos[0] += tswUtilsLeftBorder(parent);
				pos[1] += tswUtilsTopBorder(parent);
			}
		} 
		else if(element != orig && isWebkit)
		{
			pos[0] += tswUtilsLeftBorder(element);
			pos[1] += tswUtilsTopBorder(element);
		}
		element = element.offsetParent;
	}
	if(isGecko && !tswUtilsBorderBox(orig))
	{
		pos[0] -= tswUtilsLeftBorder(orig);
		pos[1] -= tswUtilsTopBorder(orig);
	}
	
	return pos;
}

//Returns the visible rect that the user can see in the browser window [x,y,width,height].
function tswUtilsGetVisibleRect()
{
	var width, height, x, y;
	
	//From http://thewebdevelopmentblog.com/2008/10/tutorial-pop-overs-part-2-centering-the-pop-over/
    if (document.all) 
	{
		// IE
		width  = (document.documentElement.clientWidth) ? 
		document.documentElement.clientWidth : 
		document.body.clientWidth;
		height = (document.documentElement.clientHeight) ? 
		document.documentElement.clientHeight : 
		document.body.clientHeight;
		y = (document.documentElement.scrollTop) ? 
		document.documentElement.scrollTop : 
		document.body.scrollTop;
		x = (document.documentElement.scrollLeft) ? 
		document.documentElement.scrollLeft : 
		document.body.scrollLeft;
		
    } 
	else 
	{
		// Safari, Firefox
		width = window.innerWidth;
		height = window.innerHeight;
		y = window.pageYOffset;
		x = window.pageXOffset;
	}
	
	return [x, y, width, height];
}

//Takes a pixel value, which may end in 'px' and returns the integer portion
function tswUtilsGetPixelsAsInteger(pixelValue)
{
	var str = String(pixelValue);
	var val = parseInt(str.replace('px', ''));
	if(isNaN(val))
	{
		return 0;
	}
	return val;
}

//Get the currently applied style property value for an element.
function tswUtilsGetStyle(el, cssprop)
{
	if (el.currentStyle) //IE
		return el.currentStyle[cssprop]
	else if (document.defaultView && document.defaultView.getComputedStyle) //Firefox
		return document.defaultView.getComputedStyle(el, "")[cssprop]
	else //try and get inline style
		return el.style[cssprop]
}

//Add an event handler; eventName is the name of an event (e.g. 'click') and
//funct is a function; the event will be passed to funct as a parameter
function tswUtilsAddEventHandler(obj, eventName, funct)
{
	if(obj.addEventListener)
	{
		obj.addEventListener(eventName, funct, false);
	}
	else if(obj.attachEvent)
	{
		obj.attachEvent('on'+eventName, funct);
	}
}

function tswUtilsCancelBubble(e)
{
	if (!e && !(e = window.event))
		return;
	e.cancelBubble = true;
	if (e.stopPropagation) e.stopPropagation();
}

function tswUtilsGetInitializedEvent(e)
{
	var evt = window.event || e;
	if(!evt.target) //if event obj doesn't support e.target, presume it does e.srcElement
		evt.target=evt.srcElement //extend obj with custom e.target prop
		return evt;
}

/* The checksum below is for internal use by Taco HTML Edit, 
   to detect if a component file has been modified.
   TacoHTMLEditChecksum: 7A74BA81 */