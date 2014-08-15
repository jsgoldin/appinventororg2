/* =============================================================
 * Copyright AppInventor.org 2012
 * Scripts by J.D. Manuel
 * ============================================================ */



function prepareContactForm()
{
	document.getElementById('contactClick').onclick = function()
	{
		document.getElementById('contactForm').style.display = "block";		
	}
	
	// hides contact form on page load
	document.getElementById('contactForm').style.display = "none";
}

window.onload = function()
{
	//prepareContactForm();
	// other prep functions called here
	
}
  
$(document).ready(function(){
	$('#banner_top').animate({opacity:1}, 1500);
});