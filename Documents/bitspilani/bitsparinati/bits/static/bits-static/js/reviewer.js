$( document ).ready(function() {

	$('#example').dataTable( { 
    			"searching": false,
    			"lengthChange": false,
    			"iDisplayLength": 100,
    			 } );

	
	var total_form = $('#id_doc-TOTAL_FORMS').val();
	var bits_rejection_id = '#id_bits_rejection_reason';
	var rejection_comments_id = '#id_selection_rejection_comments';
	var accepted_verified_flag = 'accepted_verified_by_bits_flag';
	var file_link ='file_link';
	var deffered_submission_flag = 'deffered_submission_flag';
	var rejected_flag = 'rejected_by_bits_flag';
	var rejection_reason = 'rejection_reason';
	var exception_notes='exception_notes'
	var prefix = 'doc';
	var id_prefix = 'id_' + prefix;
	for (var i=0; i<total_form; i++)
	{
		var accepted_verified_flag_id = id_prefix + '-' + i + '-' + accepted_verified_flag;
		var rejected_flag_id = id_prefix + '-' + i + '-' + rejected_flag;
		var deffered_submission_flag_id = id_prefix + '-' + i + '-' + deffered_submission_flag;
		var rejected_reason_id = id_prefix + '-' + i + '-' + rejection_reason;
		var file_link_id = id_prefix + '-' + i + '-' + file_link;
		var exception_notes_id = id_prefix + '-' + i + '-' + exception_notes;

		if ($('#'+accepted_verified_flag_id).is(':checked'))
		{
			$('#' + rejected_flag_id).prop('checked', false);
			$('#' + deffered_submission_flag_id).prop('checked', false);
			$('#' + rejected_reason_id).val('').prop('disabled',true);
		}
		else if($('#'+rejected_flag_id).is(':checked'))
		{
			$('#' + accepted_verified_flag_id).prop('checked', false);
			$('#' + deffered_submission_flag_id).prop('checked', false);
			$('#' + rejected_reason_id).prop('disabled',false);
		}
		else if($('#'+deffered_submission_flag_id).is(':checked'))
		{
			$('#' + accepted_verified_flag_id).prop('checked', false);
			$('#' + rejected_flag_id).prop('checked', false);
			$('#' + rejected_reason_id).prop('disabled',true);
		}
		else{
			$('#' + rejected_reason_id).prop('disabled',true);
		}

		if (form_to_be_enabled && 
			!$('#'+accepted_verified_flag_id).is(':checked') &&
			$('#' + file_link_id).attr('href') != '#'
			)
		{
			$('#' + accepted_verified_flag_id).prop('disabled',false);
			$('#' + rejected_flag_id).prop('disabled',false);
			$('#' + exception_notes_id).prop('disabled',false);
		}

	}

	if($('#id_application_status option:selected').text() == 'Rejected')
	{
		$(bits_rejection_id).prop('disabled',false);
		$(rejection_comments_id).prop('disabled',false);
	}
	else
	{
		$(bits_rejection_id).prop('disabled',true);
		$(rejection_comments_id).prop('disabled',true);
	}

	$('#doc-form select').change(function() {

		for(var i=0; i<total_form; i++)
		{
			var rejected_reason_id = id_prefix + '-' + i + '-' + rejection_reason;
			if(this.id==rejected_reason_id)
			
				$('#' + rejected_reason_id).siblings('span').html('');
		}

	});

	$('#doc-form :input[type=checkbox]').change(function() {  
		var form_index = this.id.split('-')[1]; 
		var accepted_verified_flag_id = id_prefix + '-' + form_index + '-' + accepted_verified_flag;
		var rejected_flag_id = id_prefix + '-' + form_index + '-' + rejected_flag;
		var deffered_submission_flag_id = id_prefix + '-' + form_index + '-' + deffered_submission_flag;
		var rejected_reason_id = id_prefix + '-' + form_index + '-' + rejection_reason;
		if (this.checked) {
			if (accepted_verified_flag_id == this.id)
			{
			
				$('#' + rejected_flag_id).prop('checked', false);
				$('#' + deffered_submission_flag_id).prop('checked', false);
				$('#' + rejected_reason_id).val('').prop('disabled',true);
			}
			else if (rejected_flag_id == this.id)
			{
				
				$('#' + accepted_verified_flag_id).prop('checked', false);
				$('#' + deffered_submission_flag_id).prop('checked', false);
				$('#' + rejected_reason_id).prop('disabled',false);
			}
			else if (deffered_submission_flag_id == this.id)
			{
				
				$('#' + accepted_verified_flag_id).prop('checked', false);
				$('#' + rejected_flag_id).prop('checked', false);
				$('#' + rejected_reason_id).prop('disabled',true);
			}
			
		} 
		else {
			$('#' + rejected_reason_id).val('').prop('disabled',true);
			$('#' + accepted_verified_flag_id).prop('checked', false);
			$('#' + rejected_flag_id).prop('checked', false);
			$('#' + deffered_submission_flag_id).prop('checked', false);

		}
	});

	$('#id_application_status').change(function() {
		if ($('#id_application_status option:selected').text() == 'Rejected')
		{
			$(bits_rejection_id).prop('disabled',false);
			$(rejection_comments_id).prop('disabled',false);
		}
		else
		{
			$(bits_rejection_id).prop('disabled',true);
			$(rejection_comments_id).prop('disabled',true);
			$(bits_rejection_id).val('');
			$(rejection_comments_id).val('');
		}
	});

	$('#doc-form').submit(function() { 
		for(var i=0; i<total_form; i++)
		{

			var rejected_flag_id = id_prefix + '-' + i + '-' + rejected_flag;
			var rejected_reason_id = id_prefix + '-' + i + '-' + rejection_reason;
			var accepted_verified_flag_id = id_prefix + '-' + i + '-' + accepted_verified_flag;
			var file_link_id = id_prefix + '-' + i + '-' + file_link;
			var deffered_submission_flag_id = id_prefix + '-' + i + '-' + deffered_submission_flag;
			if ($('#' + rejected_flag_id).is(':checked') && !$('#' + rejected_reason_id).val())
			{
				
				$('#' + rejected_reason_id).siblings('span').html('Please Select Rejection Reason');
				return false;
			}

			if(
				$('#id_application_status option:selected').text() == 'Shortlisted' && 
				!$('#' + accepted_verified_flag_id).is(':disabled') &&
				!(
					$('#' + accepted_verified_flag_id).is(':checked') || 					
					$('#' + deffered_submission_flag_id).is(':checked')
				)	
			)
			{
				$('#' + accepted_verified_flag_id).siblings('span').html('Please Select the document');
				return false;

			}
		}

		if (
				$('#id_application_status option:selected').text() == 'Rejected' &&
				!$('#id_bits_rejection_reason').val()
			)
		{
			$('#id_bits_rejection_reason_error').html('Please Select rejection reason');
			return false;
		}
		return true;
	});

});

