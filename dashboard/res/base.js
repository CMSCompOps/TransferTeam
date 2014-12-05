$(document).ready(function(){
    $(".basis-6").tooltip({title: 'at least one file in the block has no source replica remaining'})
    $(".basis-5").tooltip({title: 'for at least one file in the block, there is no path from source to destination'})
    $(".basis-4").tooltip({title: 'subscription was automatically suspended by router for too many failures'})
    $(".basis-3").tooltip({title: 'there is no active download link to the destination'})
    $(".basis-2").tooltip({title: 'subscription was manually suspended'})
    $(".basis-1").tooltip({title: 'block is still open'})
    $(".basis0").tooltip({title: 'all files in the block are currently routed. FileRouter estimate is used to calculate ETA'})
    $(".basis1").tooltip({title: 'the block is not yet routed because the destination queue is full'})
    $(".basis2").tooltip({title: 'at least one file in the block is currently not routed, because it recently failed to transfer, and is waiting for rerouting'})

});

