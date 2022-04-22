$( document ).ready(function() {
		var total_form = $('#id_doc-TOTAL_FORMS').val();
		var accepted_verified_flag = 'accepted_verified_by_bits_flag';
		var rejected_flag = 'rejected_by_bits_flag';
		var rejection_reason = 'rejection_reason';
		var deffered_submission_flag = 'deffered_submission_flag';
		var prefix = 'doc';
		var id_prefix = 'id_' + prefix;
		for (var i=0;i<total_form;i++)
		{
			var accepted_verified_flag_id = id_prefix + '-' + i + '-' + accepted_verified_flag;
			var rejected_flag_id = id_prefix + '-' + i + '-' + rejected_flag;
			var rejected_reason_id = id_prefix + '-' + i + '-' + rejection_reason;
			var deffered_submission_flag_id = id_prefix + '-' + i + '-' + deffered_submission_flag;

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

		}

		$('#doc-form select').change(function() {

			for(var i=0;i<total_form;i++)
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

	$('#doc-form').submit(function() { 
		for(var i=0;i<total_form;i++)
		{

			var rejected_flag_id = id_prefix + '-' + i + '-' + rejected_flag;
			var rejected_reason_id = id_prefix + '-' + i + '-' + rejection_reason;
			if ($('#' + rejected_flag_id).is(':checked') && !$('#' + rejected_reason_id).val())
			{
				
				$('#' + rejected_reason_id).siblings('span').html('Please Select Rejection Reason');
				return false;
			}

		}
		if(!$('#id_application_status').val())
		{
			$('#id_app_form_error').html('Please Select Status');
			return false;
		}
		return true;
	});

});
    
