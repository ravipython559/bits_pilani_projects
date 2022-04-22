(function($) {

	$( document ).ready(function() {
        
		$("#id_program").change(function(){
			 program = $(this).val();
		     $.get( $("#id_ajax_url").val() , { 'program': program }).done(function( data ){ 
                    $("#id_course_id_slot").empty();
                    $.each(data,function(key,value){
                    $("#id_course_id_slot").append($('<option>',{value:key,text:value}));
                           });
                });  
            });	
        });

}(django.jQuery))