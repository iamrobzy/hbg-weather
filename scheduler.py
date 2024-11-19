import modal

app = modal.App('scheduler')

@app.function(schedule=modal.Period(seconds=15))
def update():
    print('Updating...')