// For development/testing purposes
exports.handler = (event, context, callback) => {
  console.log('Running index.handler')
  console.log('==================================')
  console.log('event', event)
  console.log('==================================')
  console.log('Stopping index.handler')
  callback(null)
}
