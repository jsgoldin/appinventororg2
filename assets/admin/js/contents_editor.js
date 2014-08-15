/*
 *	The following is used on the contents editor page! 
 * 
 * 
 */

/**
 * Retrieves data from the new content form, and then submits it to the server.
 */



function endsWith(str, suffix) {
    return str.indexOf(suffix, str.length - suffix.length) !== -1;
}


$("#createContentbtn").click(function(event) {
	alert("create new content!")

	title = $("#new_content_title").val();
	description = $("#new_content_description").val();
	content_type = $('input:radio[name=inlineRadioOptions]:checked').val();
	file_path = $("#new_content_file_path").val();
	identifier = $('#new_content_identifier').val();
	
	// need better way to get course and module id
	course_id = $('.subject-box-top-half-inner').attr('course_id')
	module_id = $('.subject-box-top-half-inner').attr('module_id')
	
	if(file_path == "") {
		// TODO: ADD BETTER FILEPATH VALIDATION
		errorString += "\tYou must enter a filepath!\n";
		validate = false;
	} else {
		// make sure filepath ends with no redirect flag
		if(!endsWith(file_path, "?flag=true")) {
			file_path += "?flag=true"
		}
		
	}

	
	validated = true;
	errorString = "Missing required fields\n\n";

	if (title == "") {
		errorString += "\tYou must enter a title!\n";
		validated = false;
	}

	if (content_type == undefined) {
		errorString += "\tYou must choose a type!\n";
		validated = false;
	}
	

	if (validated) {
		// submit it!
		$.post("/admin/course_system/create/Content", {
			s_title : title,
			s_description : description,
			s_file_path : file_path,
			s_content_type : content_type,
			s_course_id : course_id,
			s_module_id : module_id,
			s_identifier : identifier
		}, function(data, status) {
			location.reload(true)
		});
	} else {
		alert(errorString)
	}
});


$(document).ready(function() {

	// true if mouseover noclick element, false otherwise
	var insideNoClick = false;

	/* Clickable item boxes that take you to corresponding content page */
	$(document).on('click', '.module-edit-box', function() {
		if (insideNoClick == true) {
			// alert("NO LINK!");
		} else {
			window.location = document.URL + "/" + $(this).attr('identifier');
		}
	});

	/* Highlight item boxes on hover */
	$(".module-edit-box").mouseover(function() {
		$(this).addClass('hover');
		$(this).find(".item-box-btns").removeClass('hidden');
	});

	$(".module-edit-box").mouseout(function() {
		$(this).removeClass('hover');
		$(this).find(".item-box-btns").addClass('hidden');
	});

	/* Delete content button */
	$(document).on('click', '#deletemodulebtn', function() {
		s_content_id = $(this).parent().parent().attr('keyid');
		s_module_id = $('.subject-box-top-half-inner').attr("module_id")
		s_course_id = $('.subject-box-top-half-inner').attr("course_id")

		$.post("/admin/course_system/delete/Content", {
			content_id : s_content_id,
			module_id : s_module_id,
			course_id : s_course_id
		}, function(data, status) {
			location.reload(true)

		});
	});

	



	/* Allow drag and drop */
	$(function() {
		$("#sortable").sortable({
			cancel : "#noDrag",
			stop : function(event, ui) {
				saveOrder();

			}
		});
	});

	function saveOrder() {
		var index = -1;
		var resultArray = "";
		var module_id = $(".subject-box-top-half-inner").attr('module_id');
		var course_id = $(".subject-box-top-half-inner").attr('course_id');
		$("#sortable").children().each(function() {
			resultArray += ++index + ",";
			resultArray += $(this).attr('keyid') + ",";
		});

		$.post("/admin/course_system/reorder/Content", {
			s_course_id : course_id,
			s_module_id : module_id,
			s_resultArray : resultArray,
		}, function(data, status) {
			location.reload(true);
		});

	}

	/* Move module button */
	$(document).on('mouseover', '#movemodulebtn', function() {
		$(this).parent().parent().attr('id', '');
	});

	$(document).on('mouseout', '#movemodulebtn', function() {
		$(this).parent().parent().attr('id', 'noDrag');
	});

	/* Prevent certain items from linking to content page on click */
	$(document).on('mouseover', '.noclick', function() {
		insideNoClick = true;
	});

	$(document).on('mouseout', '.noclick', function() {
		insideNoClick = false;
	});
	
	
	
	/* edit button */
	$(document).on('click', '#editmodulebtn', function() {
		// get current attributes of content 
		
		content_root = $(this).parent().parent();
		title = content_root.find('h1');
		description = content_root.find('p');
		
		content_type = content_root.attr('content_type');
		
		url = content_root.attr('content_url');
		
		editableURL = url.substring(0,url.indexOf('?'));
		
		identifier = content_root.attr('identifier');
		
		// set modal form inputs to current content values
		$('#edit_content_title').val(title.text());
		$('#edit_content_description').val(description.text());
		$('#edit_content_url').val(editableURL);
		$('#edit_content_identifier').val(identifier);
		$('#radioForm' + content_type).attr('checked', true);
		
		// set some sneaky modal attributes for later XP
		$('#editModal').attr('content_id', content_root.attr('keyid'));
	});
	
	/* update content */
	$('#updateContent').click(function() {
		
		
		content_id = $('#editModal').attr('content_id');
		module_id = $('.subject-box-top-half-inner').attr('module_id');
		course_id = $('.subject-box-top-half-inner').attr('course_id');
		
		title = $('#edit_content_title').val();
		description = $('#edit_content_description').val();
		url = $('#edit_content_url').val();
		identifier = $('#edit_content_identifier').val();
		
		content_type = $('input:radio[name=editinlineRadioOptions]:checked').val();

		if (title == "") {
			alert("title cannot be empty!")
		} else {
			
			// make sure filepath ends with no redirect flag
			if(!endsWith(url, "?flag=true")) {
				url += "?flag=true"
			}
			
			$.post("/admin/course_system/update/Content", {
				s_content_id : content_id,
				s_module_id : module_id,
				s_course_id : course_id,
				s_title : title,
				s_description : description,
				s_url : url,
				s_content_type : content_type,
				s_identifier : identifier
			}, function(data, status) {
				location.reload(true);
			});
		}
	});
});