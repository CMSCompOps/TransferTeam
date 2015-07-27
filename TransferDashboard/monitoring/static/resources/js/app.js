(function(window, $) {

  /*
   * SORTABLE TABLE
   */

  var SortableTable = function(elem, options) {
    var self = this;
    self.elem = elem;
    self.init(options);
  };

  SortableTable.DEFAULTS = {
    test: 5
  };

  SortableTable.prototype.init = function(options) {
    var self = this;
    self.sortableColumns = self.elem.find('[data-func="sortable"]');
    self.rows = self.elem.find('tbody > tr');
    
    // add icon for sortable columns
    self.sortableColumns.append('<span class="glyphicon glyphicon-sort" aria-hidden="true"></span>');
    
    // data to keep the sorting order
    self.sortableColumns.data('order', false);
    
    self.sortableColumns.click(function(e) {
      self.sort($(this));
    });
  };
  
  SortableTable.prototype.sort = function(col) {
    var self = this;
    console.log(col);
    var index = col.index() + 1;

    // sort the elements
    self.rows.sort(function(a,b) {
      var keyA = $('td:nth-child('+index+')', a).text();
      var keyB = $('td:nth-child('+index+')', b).text();

      if(col.data('order')){
        return (keyA > keyB) ? 1 : -1;
      } else {
        return (keyA < keyB) ? 1 : -1;
      }
    });
    
    // update data to keep track of the sorting order
    col.data('order', !col.data('order'));
    
    // add them back into parent
    $.each(self.rows, function(index, row){
        self.elem.append(row);
    });
  }

  $.fn.sortableTable = function(options) {
    return this.each(function() {
      new SortableTable($(this), options);
    });
  };

  $(window).on('load', function () {
    // for each module element in the HTML, create corresponding JS Object
    $('[data-module="sortable-table"]').sortableTable();
  });
  
}(window, jQuery));
