(function(){
  function debounce(fn, delay){let t;return function(){clearTimeout(t);const args=arguments;t=setTimeout(()=>fn.apply(this,args),delay)}}
  async function createPlacesSession(){
    try{
      const res=await fetch('/api/places/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({purpose:'workplace_search'})});
      if(!res.ok){return ''}
      const data=await res.json();
      return data.session_token||'';
    }catch(e){return ''}
  }
  async function fetchSuggestions(input){
    const q=input.value.trim();
    if(q.length<2){return []}
    if(!input.dataset.sessionToken){input.dataset.sessionToken=await createPlacesSession()}
    const token=input.dataset.sessionToken||'';
    const url='/api/places/autocomplete?q='+encodeURIComponent(q)+'&session_token='+encodeURIComponent(token);
    const res=await fetch(url);
    if(!res.ok){return []}
    return await res.json();
  }
  async function confirmPlace(input,item,target,panel){
    input.value=item.description;
    if(target){target.value=item.place_id||''}
    try{
      await fetch('/api/places/confirm',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_token:input.dataset.sessionToken||'',place_id:item.place_id||'',description:item.description})});
    }catch(e){}
    input.dataset.sessionToken='';
    if(panel){panel.hidden=true}
  }
  function setupAutocomplete(input){
    const panel=input.parentElement.querySelector('.autocomplete-panel');
    const targetId=input.dataset.placeTarget;
    const target=targetId?document.getElementById(targetId):null;
    const run=debounce(async()=>{
      const items=await fetchSuggestions(input);
      if(!panel){return}
      panel.innerHTML='';
      if(!items.length){panel.hidden=true;return}
      const header=document.createElement('div');
      header.className='autocomplete-header';
      header.textContent='Did you mean this workplace address?';
      panel.appendChild(header);
      items.forEach(item=>{
        const btn=document.createElement('button');
        btn.type='button';
        btn.className='autocomplete-option';
        btn.innerHTML='<strong>'+item.main_text+'</strong><br><span>'+((item.secondary_text)||item.description)+'</span>';
        btn.addEventListener('click',()=>confirmPlace(input,item,target,panel));
        panel.appendChild(btn);
      });
      panel.hidden=false;
    },250);
    input.addEventListener('input',()=>{if(target){target.value=''};run()});
    input.addEventListener('focus',()=>{if(!input.dataset.sessionToken){createPlacesSession().then(token=>{input.dataset.sessionToken=token})}});
    document.addEventListener('click',(ev)=>{if(panel && !input.parentElement.contains(ev.target)){panel.hidden=true}});
  }
  function setupMapPreview(){
    document.querySelectorAll('[data-listings]').forEach(el=>{
      let items=[];
      try{items=JSON.parse(el.dataset.listings||'[]')}catch(e){items=[]}
      if(!items.length){return}
      const count=document.createElement('div');
      count.className='map-summary';
      count.innerHTML='<strong>'+items.length+' mapped rentals</strong><br><span>Interactive map integration is ready for Google Maps JS. Pins are already exposed through the API.</span>';
      el.appendChild(count);
    });
  }

  window.initRnwMap=function(){
    const el=document.getElementById('rnw-map');
    if(!el || !window.google || !google.maps){return}
    let listings=[];
    try{listings=JSON.parse(el.dataset.listings||'[]')}catch(e){listings=[]}
    const originLat=parseFloat(el.dataset.originLat||'');
    const originLng=parseFloat(el.dataset.originLng||'');
    const hasOrigin=!Number.isNaN(originLat)&&!Number.isNaN(originLng);
    const center=hasOrigin?{lat:originLat,lng:originLng}:(listings[0]?{lat:listings[0].lat,lng:listings[0].lng}:{lat:-29.8587,lng:31.0218});
    el.innerHTML='';
    const map=new google.maps.Map(el,{center:center,zoom:hasOrigin?13:11,mapTypeControl:false,streetViewControl:false,fullscreenControl:true});
    const bounds=new google.maps.LatLngBounds();
    if(hasOrigin){
      const pos={lat:originLat,lng:originLng};
      new google.maps.Marker({position:pos,map:map,label:'W',title:el.dataset.originLabel||'Workplace'});
      bounds.extend(pos);
    }
    listings.forEach(item=>{
      const pos={lat:Number(item.lat),lng:Number(item.lng)};
      const marker=new google.maps.Marker({position:pos,map:map,title:item.title,label:'R'});
      const info=new google.maps.InfoWindow({content:'<strong>'+item.title+'</strong><br>R'+item.rent+' / month<br><a href="'+item.url+'">View rental</a>'});
      marker.addListener('click',()=>info.open({anchor:marker,map:map}));
      bounds.extend(pos);
    });
    if(listings.length || hasOrigin){map.fitBounds(bounds,{top:40,right:40,bottom:40,left:40})}
  };

  document.querySelectorAll('.address-autocomplete').forEach(setupAutocomplete);
  setupMapPreview();
})();
