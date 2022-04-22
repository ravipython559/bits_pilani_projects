(function($) {

	$( document ).ready(function() {

		if ($('#id_program_type').val() !='certification')
			$('#id_enable_pre_selection_flag').prop('disabled',true);

		$('#id_program_type').on('change',function(e){
			$('#id_enable_pre_selection_flag').prop('disabled',true);
			$('#id_enable_pre_selection_flag').prop('checked',false);
			if( $( this ).val() == 'specific'){
				$('#id_hr_cont_req').prop('checked',false);
				$('#id_mentor_id_req').prop('checked',false);
				
			}
			else if ($( this ).val() == 'non-specific' ||
				$( this ).val() == 'cluster'
				){
				$('#id_hr_cont_req').prop('checked',true);
				$('#id_mentor_id_req').prop('checked',true);

			}
			else if ($( this ).val() == 'certification')
				$('#id_enable_pre_selection_flag').prop('disabled',false);
		});
  	
});
    
}(django.jQuery))
