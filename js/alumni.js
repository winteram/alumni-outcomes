function initAlumni(fileloaded,crawled)
{
  console.log('initAlumni called: ' + fileloaded + "," + crawled);
  if( fileloaded==true )
  {
    $('#progress-wrapper').show();
    var progressbar = $( "#progressbar" ), progressLabel = $( ".progress-label" );
    progressbar.progressbar({
      value: false,
      change: function() {
        progressLabel.text( progressbar.progressbar( "value" ) + "% loaded" );
      },
      complete: function() {
        progressLabel.text( "Complete!" );
      }
    });
    progressbar.progressbar( "value", 0 );
    console.log("Progressbar shown");
    parseFile();
  }
  if( crawled==true)
  {
    $('#progress-wrapper').show();
    var progressbar = $( "#progressbar" ), progressLabel = $( ".progress-label" );
    progressbar.progressbar({
      value: false,
      change: function() {
        progressLabel.text( progressbar.progressbar( "value" ) + "% crawled" );
      },
      complete: function() {
        progressLabel.text( "Complete!" );
      }
    });
    progressbar.progressbar( "value", 0 );
    console.log('Begin crawl');
    doCrawl();
  }
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

function parseFile(offset)
{
  $('#progress-wrapper').show();
  console.log("parseFile called");
  offset = typeof offset !== 'undefined' ? offset : 0;
  $.post('/extras',{'func':'parsefile','limit':'100','offset':offset},function(data) {
    if (data.hasOwnProperty('complete')) { 
      console.log('posted successfully');
      var progressbar = $( "#progressbar" ), progressLabel = $( ".progress-label" );
      progressbar.progressbar({
        value: false,
        change: function() {
          progressLabel.text( progressbar.progressbar( "value" ) + "% loaded" );
        },
        complete: function() {
          progressLabel.text( "Complete!" );
        }
      });
      console.log("Progressbar initiated");
      progress_val = Math.round(10000 * data.offset / data.N) / 100;
      progressbar.progressbar( "value", progress_val );
      console.log("parsefile returned, complete is " + data.complete);
      console.log("Offset is " + data.offset);
      if (data.complete=='false') {
        parseFile(data.offset);
      } else {
        progressbar.progressbar( "value", 100);
        //doCrawl();
        alert('file loaded!');
      }
    }
  }, "json");
}

function doCrawl(ncrawled)
{
  ncrawled = typeof ncrawled !== 'undefined' ? ncrawled : 0;
  $('#progress-wrapper').show();
  $.post('/crawl',{'limit':10,'ncrawled':ncrawled},function(data) {
    if (data.hasOwnProperty('error')) { 
      console.log(data.error);
    }
    else if (data.hasOwnProperty('throttled')) { 
      console.log('data throttled');
      var progressbar = $( "#progressbar" ), progressLabel = $( ".progress-label" );
      progressbar.progressbar({
        value: false,
        change: function() {
          progressLabel.text( progressbar.progressbar( "value" ) + "% crawled" );
        },
        complete: function() {
          progressLabel.text( "Complete!" );
        }
      });
      var progressbar = $( "#progressbar" ), progressLabel = $( ".progress-label" );
      progress_val = Math.round(10000 * data.ncrawled / data.N) / 100;
      progressbar.progressbar( "value", progress_val );
      progressLabel.text( progressbar.progressbar( "value" ) + "% crawled: Throttled" );
      console.log('Throttled: create visualizations!');
      doViz();
    }
    else if (data.hasOwnProperty('ncrawled')) { 
      var progressbar = $( "#progressbar" ), progressLabel = $( ".progress-label" );
      progressbar.progressbar({
        value: false,
        change: function() {
          progressLabel.text( progressbar.progressbar( "value" ) + "% crawled" );
        },
        complete: function() {
          progressLabel.text( "Complete!" );
        }
      });
      progress_val = Math.round(10000 * data.ncrawled / data.N) / 100;
      progressbar.progressbar( "value", progress_val );
      if (data.ncrawled==data.N) {
        progressbar.progressbar( "value", 100);
        console.log('Finished: create visualizations!');
        doViz();
      } else {
        doCrawl(data.ncrawled);
      }
    }
  }, "json");
}

function doViz()
{
  $('#progress-wrapper').show();
  $('.d3vis').show();
  $.post('/viz',{'viz':'pctmatch'}, function(data)
  {
    matchstr = "<span class='pctmatch'>" + data.pctmatch + "</span>";
    matchstr += "<span class='pctmatch-pct'>%</span>";
    matchstr += "<span class='pctmatch-txt'> of crawled names had a matching LinkedIn Profile</span>";
    $('#percent-match').html(matchstr);
  },"json");

  $.post('/viz',{'viz':'piecountry'}, function(data)
  {
    var width = 300,
    height = 250,
    radius = Math.min(width, height) / 2;

    var color = d3.scale.ordinal()
        .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"]);

    var arc = d3.svg.arc()
        .outerRadius(radius - 10)
        .innerRadius(0);

    var pie = d3.layout.pie()
        .sort(null)
        .value(function(d) { return d.freq; });

    var svg = d3.select("#countrypie").append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

    var g = svg.selectAll(".arc")
        .data(pie(data.pdata))
        .enter().append("g")
        .attr("class", "arc");

    g.append("path")
        .attr("d", arc)
        .style("fill", function(d) { return color(d.data.country); });

    g.append("text")
        .attr("transform", function(d) { return "translate(" + arc.centroid(d) + ")"; })
        .attr("dy", "1.5em")
        .style("text-anchor", "middle")
        .text(function(d) { return d.data.country; });

    otherlist = '<div style="font-weight:bold">Frequencies</div>';
    for (i=0; i<data.clist.length; i++)
    {
      otherlist += '<div class="othercountry">' + data.clist[i].country + ': ' + data.clist[i].freq + '</div>';
    }
    $('#countrylist').html(otherlist);
  },"json");

  $.post('/viz',{'viz':'histregion'}, function(data)
  {
    var margin = {top: 20, right: 20, bottom: 30, left: 40},
    width = 500 - margin.left - margin.right,
    height = data.length * 25 + margin.top + margin.bottom;
    
    var svg = d3.select("#regions").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g");
//        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var formatPercent = d3.format(".0%");
    
    var x = d3.scale.linear()
        .range([0, width]);
    
    var y = d3.scale.ordinal()
        .rangeRoundBands([0, height], .1);

    x.domain([0, d3.max(data, function(d) { return d.freq; })]);
    y.domain(data.map(function(d) { return d.region; }));

    svg.selectAll(".bar")
        .data(data)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("x", 200)
        .attr("width", function(d) { return x(d.freq); })
        .attr("y", function(d) { return y(d.region); })
        .attr("height", y.rangeBand());

    svg.selectAll(".rname")
        .data(data)
        .enter().append("text")
        .attr("x", 190)
        .attr("y", function(d) { return y(d.region) + y.rangeBand()/2; } )
        .attr("dy", ".35em")
        .attr("text-anchor", "end")
        .attr('class', 'rname')
        .text(function(d) { return d.region; } );

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
        .tickFormat(formatPercent);

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

    svg.append("g")
        .attr("class", "x axis")
        //.attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis);
/*        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Frequency"); */

  },"json");


  $.post('/viz',{'viz':'histindustry'}, function(data)
  {
    var margin = {top: 20, right: 20, bottom: 30, left: 40},
    width = 500 - margin.left - margin.right,
    height = data.length * 25 + margin.top + margin.bottom;
    
    var svg = d3.select("#industries").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g");
//        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var formatPercent = d3.format(".0%");
    
    var x = d3.scale.linear()
        .range([0, width]);
    
    var y = d3.scale.ordinal()
        .rangeRoundBands([0, height], .1);

    x.domain([0, d3.max(data, function(d) { return d.freq; })]);
    y.domain(data.map(function(d) { return d.industry; }));

    svg.selectAll(".bar")
        .data(data)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("x", 200)
        .attr("width", function(d) { return x(d.freq); })
        .attr("y", function(d) { return y(d.industry); })
        .attr("height", y.rangeBand());

    svg.selectAll(".rname")
        .data(data)
        .enter().append("text")
        .attr("x", 190)
        .attr("y", function(d) { return y(d.industry) + y.rangeBand()/2; } )
        .attr("dy", ".35em")
        .attr("text-anchor", "end")
        .attr('class', 'rname')
        .text(function(d) { return d.industry; } );

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
        .tickFormat(formatPercent);

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

    svg.append("g")
        .attr("class", "x axis")
        //.attr("transform", "translate(0," + height + ")")
        .call(xAxis);

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis);
/*        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Frequency"); */

  },"json");
}

