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

var TSWDomUtils = new Object; //object for static method calls

//Returns an array of children of element with name tagName; as opposed to getElementsByTagName
//which returns any descendant.
TSWDomUtils.getChildrenWithTagName = function(element, tagName)
{
	tagName = tagName.toUpperCase();
	var results = new Array();
	var children = element.childNodes;
	for(var i=0; i<children.length; i++)
	{
		var child = children[i];
		if(child.tagName != null && child.tagName.toUpperCase() == tagName)
		{
			results.push(child);
		}
	}
	return results;
};

//Get the first child of element with a particular class name.
TSWDomUtils.getChildWithClassName = function(element, className)
{
	var children = element.childNodes;
	for(var i=0; i<children.length; i++)
	{
		var child = children[i];
		if(child.tagName != null && child.className == className)
		{
			return child;
		}
	}
	return null;
};

/* The checksum below is for internal use by Taco HTML Edit, 
   to detect if a component file has been modified.
   TacoHTMLEditChecksum: BAE92AA0 */