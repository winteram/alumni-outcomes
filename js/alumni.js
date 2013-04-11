function initAlumni(fileloaded,crawled)
{
  console.log('initAlumni called: ' + fileloaded + "," + crawled);
  if( fileloaded==true)
  {
    var progressbar = $( "#progressbar" ), progressLabel = $( ".progress-label" );
    progressbar.progressbar({
      value: false,
      change: function() {
        progressLabel.text( progressbar.progressbar( "value" ) + "%" );
      },
      complete: function() {
        progressLabel.text( "Complete!" );
      }
    });
    parseFile();
  }
  if( crawled==true)
  {
    console.log('Begin crawl');
    doCrawl();
  }
}

function parseFile(offset=0)
{
  $.post('/extras',{'func':'parsefile','limit':100,'offset':offset},function(data) {
    if (data.hasOwnProperty('complete')) { 
      var progressbar = $( "#progressbar" ), progressLabel = $( ".progress-label" );
      progressbar.progressbar( "value", 100 * data.offset / data.N );
      if (data.complete) {
        progressbar.progressbar( "value", 100);
        //doCrawl();
        alert('file loaded!');
      } else {
        parseFile(data.offset);
      }
    }
  });
}

function doCrawl()
{
  $.post('/crawl',{'limit':10},function(data) {
    console.log(data);
    alert('crawled!');
  });
}

function validateTemplate()
{
  var is_valid = true;

  // verify template name is valid & create short name
  var template_name_raw = $('#new-template-form input[name=template-name]').val();
  var template_name = template_name_raw.replace('/[^0-9A-z_ -]/i','');
  if( template_name.length == 0)
  {
    alert('Please use only alphanumeric characters, underscore, hyphen and spaces for the template name');
    is_valid = false;
  }
  var template_short = template_name.replace(' ','');
  console.log("template: " + template_name);

  // verify school name is valid
  var school_name_raw = $('#new-template-form input[name=school-name]').val();
  var school_name = school_name_raw.replace('/[^A-z]/i','');
  if( school_name.length == 0)
  {
    alert('Please use only alphanumeric characters for the school name');
    is_valid = false;
  }
  console.log("school: " + school_name);

  if(is_valid) $('#new-template-form').submit();
}


function makeProgress()
{
  console.log('making progress');
  var progressbar = $( "#progressbar" ), progressLabel = $( ".progress-label" );

  progressbar.progressbar({
    value: false,
    change: function() {
      progressLabel.text( progressbar.progressbar( "value" ) + "%" );
    },
    complete: function() {
      progressLabel.text( "Complete" );
    }
  });

  function progress() {
    var template_name = $('#loaded-template-name').html();

    $.post('/extras',{'func':'progress','name':template_name},
      function(data)
      {
        if (data.hasOwnProperty('ecode')) { 
          switch(data.ecode)
          {
            case '300':
              progressbar.progressbar( "value", data.progress);
              var val = progressbar.progressbar( "value" ) || 0;
              if ( val < 99 ) {
                setTimeout( progress, 1000 );
              }
              break;
            case '302':
              progressbar.progressbar( "value", data.progress);
              $( ".progress-label" ).text( "Throttled" );
              break;
            default:
              console.log('Error in progress bar: ' + data.ecode)
          }
        } else {
          console.log('Error in progress bar: ' + data);
        }
      }, "json");
  }

  setTimeout( progress, 5000 );
}

