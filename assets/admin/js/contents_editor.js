/*
 *	The following is used on the contents editor page! 
 */

/**
 * Retrieves data from the new content form, and then submits it to the server.
 */
function endsWith(str, suffix) {
	return str.indexOf(suffix, str.length - suffix.length) !== -1;
}

/**
 * Checks that a url has a valid redirectFlag, if it doesn't it adds one.
 * Assumes no duplicate keys.
 */
function validateURLRedirect(url) {
	console.log("validating url: " + url)
	
	qI = url.indexOf("?");
	
	if (qI == -1) {
		// has no query string
		console.log("no query string was found");
		url += "?flag=true";
		return url;
	} else {
		// query string exists, check if
		// it has the redirect flag
		queryString = url.substring(qI);

		rI = queryString.indexOf("flag=true");
		if (rI == -1) {
			// no redirect flag was found
			if (queryString.length == 1) {
				// no parameters
				url += "flag=true";
				return url;
			} else {
				url += "&flag=true"
				return url;
			}
		} else {
			// redirect flag was found
			return url;
		}
	}
}


/**
 * Handles the creation of a new content item. Retrieves user inputted data from
 * fields on page, validates them, and sends them to the server.
 */
$("#createContentbtn").click(function(event) {
	title = $("#new_content_title").val();
	description = $("#new_content_description").val();
	file_path = $("#new_content_file_path").val();
	identifier = $('#new_content_identifier').val();
	old_urls = $('#new_content_old_urls').val();
	content_type = $('#new_content_type').val();
	course_id = $('.subject-box-top-half-inner').attr('course_id')
	module_id = $('.subject-box-top-half-inner').attr('module_id')

	errorString = "";

	if (file_path == "") {
		errorString += "\tYou must enter a filepath!\n";
		validate = false;
	} else {
		// make sure filepath ends with a no redirect flag
		file_path = validateURLRedirect(file_path);
	}

	validated = true;
	errorString = "Missing required fields\n\n";

	if (title == "") {
		errorString += "\tYou must enter a title!\n";
		validated = false;
	}

	if (content_type == "Choose a type:") {
		errorString += "\tYou must choose a type!\n";
		validated = false;
	}

	if (identifier == "") {
		// TODO: add better identifier validation
		errorString += "\tYou must enter an identifier!\n";
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
			s_identifier : identifier,
			s_oldurls : old_urls,
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
		identifier = content_root.attr('identifier');
		old_urls = content_root.attr('old_urls');
		if (old_urls == "[]") {
			old_urls = "";
		} else {
			// turn the list into white space separated for easy user
			// editing
			old_urls = old_urls.replace("[", ", ");
			old_urls = old_urls.replace("]", "");
			old_urls = old_urls.split(", u").join(" ");
			old_urls = old_urls.replace(" ", "");
			old_urls = old_urls.split("'").join("");
		}
		
		
		
		
		// set modal form inputs to current content values
		$('#edit_content_title').val(title.text());
		$('#edit_content_description').val(description.text());
		$('#edit_content_url').val(url);
		$('#edit_content_identifier').val(identifier);
		$('#edit_content_old_urls').val(old_urls);
		$('#edit_content_type').val(content_type);

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
		oldurls = $('#edit_content_old_urls').val();

		content_type = $('#edit_content_type').val();

		validated = true;
		errorString = "Missing required fields\n\n";

		if (title == "") {
			errorString += "\tYou must enter a title!\n";
			validated = false;
		} else {
			// make sure url ends with a no redirect flag
			url = validateURLRedirect(url);
		}

		if (content_type == "Choose a type:") {
			errorString += "\tYou must choose a type!\n";
			validated = false;
		}

		if (identifier == "") {
			// TODO: add better identifier validation
			errorString += "\tYou must enter an identifier!\n";
			validated = false;
		}

		if (validated) {
			$.post("/admin/course_system/update/Content", {
				s_content_id : content_id,
				s_module_id : module_id,
				s_course_id : course_id,
				s_title : title,
				s_description : description,
				s_url : url,
				s_content_type : content_type,
				s_identifier : identifier,
				s_oldurls : oldurls,
			}, function(data, status) {
				location.reload(true);
			});
		} else {
			alert(errorString)
		}
	});

});