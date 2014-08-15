/* Delete content button listener */
$(document).on('click', '.delete-content-button', function() {
	item = $(this).parent().parent().parent();
	item.remove();

});

/* Delete module button */
$(document).on('click', '.delete-module-button', function() {
	$(this).parent().parent().parent().parent().attr('delFlag', 'true');
	$(this).parent().parent().parent().parent().hide();
});

/* Open module button */
$(document).on('click', '.open-module-button', function() {
	
	s_keyid = $(this).parent().parent().parent().parent().attr('keyid');
	
	window.location = "/admin/content?keyid=" + s_keyid

});



$("#savebtn").click(function() {
	alert("saving changes!");

	/* Iterate through every module */

	$("#sortable").children().each(function() {

		s_icon = $(this).find("img").attr('src');
		s_title = $(this).find("h1").html();
		s_description = $(this).find("p").html();

		s_keyId = $(this).attr('keyId');
		s_delFlag = $(this).attr('delFlag');
		
		
		$.post("/admin/modules", {
			icon : s_icon,
			title : s_title,
			description : s_description,
			keyId : s_keyId,
			delFlag : s_delFlag
		}, function(data, status) {
			// alert("Status: " + status);
		});
	});
});

/* Create new form submit function */

$("#NewModuleForm").submit(		
		function(event) {
			event.preventDefault();
		

			new_title = $("#InputTitle").val();
			new_description = $("#InputDescription").val();
			new_icon = $("#InputFile").files;

			file = $('#InputFile').get(0).files[0];
			
			var reader = new FileReader();
			
			var dataURL = null;
			
			// Closure to capture the file information.
		    reader.onload = (function(theFile)
		    {
		    	return function(e) {
		    	dataURL = e.target.result;
		    	
		    	// add it to the module list
				$("#sortable").append(
						"<li delFlag=\"false\" keyId=\"-1\">"
						+ "<div class=\"module-info\">"
						+ "<div class=\"row\">"
						+ "<div class=\"col-md-2\">"
						+ "<img src=\""
						+ dataURL
						+ "\" height=\"100\" width=\"100\">"
						+ "</div>"
						+ "<div class=\"col-md-7\">"
						+ "<h1 id=\"noDrag\" contenteditable=\"true\">"
						+ new_title
						+ "</h1>"
						+ "<p id=\"noDrag\" contenteditable=\"true\">"
						+ new_description
						+ "</p>"
						+ "</div>"
						+ "<div class=\"col-md-2\">"
						+ "</div>"
						+ "<div class=\"col-md-1\">"
						+ "<button type=\"button\" id=\"noDrag\" class=\"btn btn-default delete-module-button\">"
						+ "<span class=\"glyphicon glyphicon-remove\"></span>"
						+ "</button>"
						+ "</div>"
						+ "</div>"
						+ "</div>" + "</div>" + "</li>");		    	
		    };
		    })(file);
		   
		    reader.readAsDataURL(file);
		    
			// reset the form
			$(this)[0].reset();		    
});

$(function() {
	$("#sortable").sortable({
		cancel : "#noDrag"
	});
});