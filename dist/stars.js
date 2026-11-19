export const starColors = ['#ffe869','#ffb54a'];
export const starPoints = Array.from({length:10}, (_, i) => {
  const angle = Math.PI/2 + i*Math.PI/5;
  const radius = i%2 ? .44 : 1;
  return [Math.cos(angle)*radius,Math.sin(angle)*radius];
});

export function starPulse(seconds, index) {
  const age = seconds % 6 - .50 - index*.095;
  if (age <= 0 || age >= 1) return 0;
  return Math.min(1,age/.18,(1-age)/.30);
}
